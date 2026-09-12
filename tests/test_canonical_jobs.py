from datetime import UTC, datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models.career import ATSBoard
from app.database.models.jobs import (
    CanonicalJob,
    JobSourcePosting,
)
from app.integrations.ats.base import (
    BoardSnapshot,
    NormalizedPosting,
)
from app.services.canonical_jobs import ingest_board_snapshot


def database_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def make_board(
    provider: str,
    token: str,
) -> ATSBoard:
    return ATSBoard(
        employer_name="Acme Corporation",
        employer_domain="acme.example",
        provider=provider,
        board_token=token,
        board_url=f"https://example.test/{token}",
        source_method="manual",
        state="live",
        posting_count=1,
        consecutive_failures=0,
        board_metadata={},
    )


def make_posting(
    *,
    external_id: str = "job-1",
) -> NormalizedPosting:
    return NormalizedPosting(
        external_id=external_id,
        title="Senior Platform Engineer",
        location="Remote - United States",
        team="Engineering",
        employment_type="Full-time",
        description_text="Build reliable cloud platforms.",
        source_url="https://example.test/jobs/job-1",
        apply_url="https://example.test/jobs/job-1/apply",
        updated_at="2026-09-12T10:00:00Z",
    )


def make_snapshot(
    provider: str,
    token: str,
    postings: tuple[NormalizedPosting, ...],
) -> BoardSnapshot:
    return BoardSnapshot(
        provider=provider,
        adapter_version=f"{provider}-test-v1",
        board_token=token,
        source_url=f"https://example.test/{token}",
        posting_count=len(postings),
        schema_hash="schema-v1",
        postings=postings,
        http_status=200,
        response_bytes=100,
    )


def test_snapshot_ingestion_is_idempotent() -> None:
    with database_session() as database:
        board = make_board("greenhouse", "acme")
        database.add(board)
        database.flush()

        snapshot = make_snapshot(
            "greenhouse",
            "acme",
            (make_posting(),),
        )

        first = ingest_board_snapshot(
            database,
            board,
            snapshot,
            observed_at=datetime.now(UTC),
        )
        second = ingest_board_snapshot(
            database,
            board,
            snapshot,
            observed_at=datetime.now(UTC),
        )

        assert first.created_sources == 1
        assert first.created_canonical_jobs == 1
        assert second.created_sources == 0
        assert second.updated_sources == 1

        canonical_count = database.scalar(select(func.count(CanonicalJob.id)))
        source_count = database.scalar(select(func.count(JobSourcePosting.id)))

        assert canonical_count == 1
        assert source_count == 1


def test_cross_source_exact_duplicate_merges() -> None:
    with database_session() as database:
        greenhouse = make_board(
            "greenhouse",
            "acme-greenhouse",
        )
        lever = make_board("lever", "acme-lever")
        database.add_all([greenhouse, lever])
        database.flush()

        posting = make_posting()

        ingest_board_snapshot(
            database,
            greenhouse,
            make_snapshot(
                "greenhouse",
                "acme-greenhouse",
                (posting,),
            ),
        )
        ingest_board_snapshot(
            database,
            lever,
            make_snapshot(
                "lever",
                "acme-lever",
                (posting,),
            ),
        )

        canonical_count = database.scalar(select(func.count(CanonicalJob.id)))
        source_count = database.scalar(select(func.count(JobSourcePosting.id)))

        assert canonical_count == 1
        assert source_count == 2


def test_missing_source_is_deactivated_and_job_closed() -> None:
    with database_session() as database:
        board = make_board("greenhouse", "acme")
        database.add(board)
        database.flush()

        ingest_board_snapshot(
            database,
            board,
            make_snapshot(
                "greenhouse",
                "acme",
                (make_posting(),),
            ),
        )

        result = ingest_board_snapshot(
            database,
            board,
            make_snapshot(
                "greenhouse",
                "acme",
                (),
            ),
        )

        source = database.scalars(select(JobSourcePosting)).one()
        canonical = database.scalars(select(CanonicalJob)).one()

        assert result.deactivated_sources == 1
        assert source.is_active is False
        assert canonical.status == "closed"


def test_canonical_url_prefers_direct_apply_url() -> None:
    with database_session() as database:
        board = make_board("lever", "acme")
        database.add(board)
        database.flush()

        ingest_board_snapshot(
            database,
            board,
            make_snapshot(
                "lever",
                "acme",
                (make_posting(),),
            ),
        )

        canonical = database.scalars(select(CanonicalJob)).one()

        assert canonical.canonical_apply_url.endswith("/apply")
