import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CareerTimestampMixin:
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


class ATSBoard(Base, CareerTimestampMixin):
    """Canonical registry entry for one employer ATS board."""

    __tablename__ = "ats_boards"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "board_token",
            name="uq_ats_boards_provider_token",
        ),
        Index("ix_ats_boards_state_next_check", "state", "next_check_at"),
        Index("ix_ats_boards_employer_domain", "employer_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    discovered_by_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    employer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    employer_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    board_token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    board_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    careers_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_method: Mapped[str] = mapped_column(
        String(30),
        default="manual",
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String(30),
        default="discovered",
        nullable=False,
        index=True,
    )
    posting_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    schema_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_successful_fetch_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    board_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )


class ATSBoardHealthCheck(Base):
    """Immutable observation produced by a coverage health worker."""

    __tablename__ = "ats_board_health_checks"
    __table_args__ = (
        Index(
            "ix_ats_health_board_checked",
            "board_id",
            "checked_at",
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
        index=True,
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    successful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    posting_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    schema_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    schema_changed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class ATSDriftAlert(Base, CareerTimestampMixin):
    """Schema-drift alert requiring adapter review."""

    __tablename__ = "ats_drift_alerts"
    __table_args__ = (Index("ix_ats_drift_status_detected", "status", "detected_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("ats_boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    previous_schema_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    observed_schema_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
