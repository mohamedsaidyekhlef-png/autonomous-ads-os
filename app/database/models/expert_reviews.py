import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
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


class ExpertReviewRun(Base):
    __tablename__ = "expert_review_runs"
    __table_args__ = (
        Index(
            "ix_expert_review_runs_org_status",
            "organization_id",
            "status",
        ),
        UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_expert_review_runs_org_idempotency",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="queued",
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(
        String(20),
        default="shadow",
        nullable=False,
    )
    analysis_engine: Mapped[str] = mapped_column(
        String(50),
        default="deterministic",
        nullable=False,
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    report_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    validation_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    report_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    rubric_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    request_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
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
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ExpertHumanReview(Base):
    __tablename__ = "expert_human_reviews"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            name="uq_expert_human_reviews_run",
        ),
        UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_expert_human_reviews_org_idempotency",
        ),
        Index(
            "ix_expert_human_reviews_org_decision",
            "organization_id",
            "decision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("expert_review_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_identity: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    reviewer_role: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    comments: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    report_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    rubric_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    request_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
