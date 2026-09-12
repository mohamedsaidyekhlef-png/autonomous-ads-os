import hashlib
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models.career import ATSBoard
from app.database.models.jobs import (
    CanonicalJob,
    JobSourcePosting,
)
from app.integrations.ats.base import BoardSnapshot, NormalizedPosting

SPACE_PATTERN = re.compile(r"\s+")
PUNCTUATION_PATTERN = re.compile(r"[^a-z0-9+#.]+")


@dataclass(frozen=True)
class IngestionResult:
    observed_postings: int
    created_sources: int
    updated_sources: int
    deactivated_sources: int
    created_canonical_jobs: int


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode(
        "ascii",
        errors="ignore",
    ).decode("ascii")
    lowercase = ascii_value.lower().strip()
    without_punctuation = PUNCTUATION_PATTERN.sub(
        " ",
        lowercase,
    )
    return SPACE_PATTERN.sub(" ", without_punctuation).strip()


def content_hash(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def canonical_dedupe_key(
    *,
    employer_domain: str,
    title: str,
    location: str | None,
    description_hash: str,
) -> str:
    identity = "|".join(
        [
            normalize_text(employer_domain),
            normalize_text(title),
            normalize_text(location),
            description_hash,
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _canonical_for_posting(
    database: Session,
    board: ATSBoard,
    posting: NormalizedPosting,
    description_digest: str,
    observed_at: datetime,
) -> tuple[CanonicalJob, bool]:
    dedupe_key = canonical_dedupe_key(
        employer_domain=board.employer_domain,
        title=posting.title,
        location=posting.location,
        description_hash=description_digest,
    )

    canonical = database.scalars(
        select(CanonicalJob).where(CanonicalJob.dedupe_key == dedupe_key)
    ).one_or_none()

    if canonical is not None:
        canonical.last_seen_at = observed_at
        canonical.status = "active"

        if posting.apply_url:
            canonical.canonical_apply_url = posting.apply_url

        return canonical, False

    canonical = CanonicalJob(
        employer_name=board.employer_name,
        employer_domain=board.employer_domain,
        normalized_employer=normalize_text(board.employer_name),
        title=posting.title,
        normalized_title=normalize_text(posting.title),
        location_text=posting.location,
        team=posting.team,
        employment_type=posting.employment_type,
        description_text=posting.description_text,
        description_hash=description_digest,
        dedupe_key=dedupe_key,
        canonical_apply_url=posting.apply_url,
        status="active",
        first_seen_at=observed_at,
        last_seen_at=observed_at,
    )
    database.add(canonical)
    database.flush()

    return canonical, True


def _upsert_source(
    database: Session,
    board: ATSBoard,
    snapshot: BoardSnapshot,
    posting: NormalizedPosting,
    observed_at: datetime,
) -> tuple[JobSourcePosting, bool, bool, uuid.UUID | None]:
    description_digest = content_hash(posting.description_text)
    canonical, canonical_created = _canonical_for_posting(
        database,
        board,
        posting,
        description_digest,
        observed_at,
    )

    source = database.scalars(
        select(JobSourcePosting).where(
            JobSourcePosting.board_id == board.id,
            JobSourcePosting.external_id == posting.external_id,
        )
    ).one_or_none()

    previous_canonical_id = None

    if source is None:
        source = JobSourcePosting(
            board_id=board.id,
            canonical_job_id=canonical.id,
            provider=snapshot.provider,
            external_id=posting.external_id,
            adapter_version=snapshot.adapter_version,
            title=posting.title,
            location_text=posting.location,
            team=posting.team,
            employment_type=posting.employment_type,
            description_text=posting.description_text,
            description_hash=description_digest,
            source_url=posting.source_url,
            apply_url=posting.apply_url,
            source_updated_at=posting.updated_at,
            is_active=True,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
        )
        database.add(source)
        source_created = True
    else:
        previous_canonical_id = source.canonical_job_id

        source.canonical_job_id = canonical.id
        source.provider = snapshot.provider
        source.adapter_version = snapshot.adapter_version
        source.title = posting.title
        source.location_text = posting.location
        source.team = posting.team
        source.employment_type = posting.employment_type
        source.description_text = posting.description_text
        source.description_hash = description_digest
        source.source_url = posting.source_url
        source.apply_url = posting.apply_url
        source.source_updated_at = posting.updated_at
        source.is_active = True
        source.last_seen_at = observed_at
        source_created = False

    database.flush()

    return (
        source,
        source_created,
        canonical_created,
        previous_canonical_id,
    )


def _refresh_canonical_status(
    database: Session,
    canonical_job_id: uuid.UUID,
) -> None:
    canonical = database.get(
        CanonicalJob,
        canonical_job_id,
    )

    if canonical is None:
        return

    active_sources = (
        database.scalar(
            select(func.count(JobSourcePosting.id)).where(
                JobSourcePosting.canonical_job_id == canonical_job_id,
                JobSourcePosting.is_active.is_(True),
            )
        )
        or 0
    )

    canonical.status = "active" if active_sources > 0 else "closed"


def ingest_board_snapshot(
    database: Session,
    board: ATSBoard,
    snapshot: BoardSnapshot,
    *,
    observed_at: datetime | None = None,
) -> IngestionResult:
    timestamp = observed_at or datetime.now(UTC)
    seen_external_ids: set[str] = set()
    affected_canonical_ids: set[uuid.UUID] = set()

    created_sources = 0
    updated_sources = 0
    created_canonical_jobs = 0

    for posting in snapshot.postings:
        if posting.external_id in seen_external_ids:
            continue

        seen_external_ids.add(posting.external_id)

        (
            source,
            source_created,
            canonical_created,
            previous_canonical_id,
        ) = _upsert_source(
            database,
            board,
            snapshot,
            posting,
            timestamp,
        )

        affected_canonical_ids.add(source.canonical_job_id)

        if previous_canonical_id is not None:
            affected_canonical_ids.add(previous_canonical_id)

        if source_created:
            created_sources += 1
        else:
            updated_sources += 1

        if canonical_created:
            created_canonical_jobs += 1

    existing_sources = database.scalars(
        select(JobSourcePosting).where(
            JobSourcePosting.board_id == board.id,
            JobSourcePosting.is_active.is_(True),
        )
    ).all()

    deactivated_sources = 0

    for source in existing_sources:
        if source.external_id in seen_external_ids:
            continue

        source.is_active = False
        source.last_seen_at = timestamp
        affected_canonical_ids.add(source.canonical_job_id)
        deactivated_sources += 1

    database.flush()

    for canonical_job_id in affected_canonical_ids:
        _refresh_canonical_status(
            database,
            canonical_job_id,
        )

    database.flush()

    return IngestionResult(
        observed_postings=len(seen_external_ids),
        created_sources=created_sources,
        updated_sources=updated_sources,
        deactivated_sources=deactivated_sources,
        created_canonical_jobs=created_canonical_jobs,
    )
