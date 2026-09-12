import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class JobTimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class CanonicalJob(Base, JobTimestampMixin):
    """One deduplicated job connected to one or more source postings."""

    __tablename__ = "canonical_jobs"
    __table_args__ = (
        UniqueConstraint(
            "dedupe_key",
            name="uq_canonical_jobs_dedupe_key",
        ),
        Index(
            "ix_canonical_jobs_status_last_seen",
            "status",
            "last_seen_at",
        ),
        Index(
            "ix_canonical_jobs_employer_title",
            "normalized_employer",
            "normalized_title",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    employer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    employer_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    normalized_employer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    normalized_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    location_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    team: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description_text: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    description_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    dedupe_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    canonical_apply_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class JobSourcePosting(Base, JobTimestampMixin):
    """Provider-specific posting linked to a canonical job."""

    __tablename__ = "job_source_postings"
    __table_args__ = (
        UniqueConstraint(
            "board_id",
            "external_id",
            name="uq_job_source_board_external",
        ),
        Index(
            "ix_job_source_canonical_active",
            "canonical_job_id",
            "is_active",
        ),
        Index(
            "ix_job_source_provider_external",
            "provider",
            "external_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("ats_boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    canonical_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("canonical_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    adapter_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    location_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    team: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    description_text: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    description_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    apply_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_updated_at: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
