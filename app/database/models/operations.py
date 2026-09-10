import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class OperationalTimestampMixin:
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


class AgentRun(Base, OperationalTimestampMixin):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_org_status", "organization_id", "status"),
        Index(
            "ix_agent_runs_org_idempotency",
            "organization_id",
            "idempotency_key",
            unique=True,
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
    status: Mapped[str] = mapped_column(
        String(30),
        default="queued",
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(
        String(30),
        default="shadow",
        nullable=False,
    )
    trigger_source: Mapped[str] = mapped_column(
        String(50),
        default="dashboard",
        nullable=False,
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    selected_agents: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    request_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class CampaignRecord(Base, OperationalTimestampMixin):
    __tablename__ = "campaign_records"
    __table_args__ = (
        Index(
            "ix_campaign_records_org_status",
            "organization_id",
            "status",
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
    advertising_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("advertising_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    platform: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    external_campaign_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(
        String(100),
        default="conversions",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
    )
    daily_budget_minor: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )


class AgentDecisionRecord(Base, OperationalTimestampMixin):
    __tablename__ = "agent_decisions"
    __table_args__ = (
        Index(
            "ix_agent_decisions_org_agent",
            "organization_id",
            "agent_id",
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
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="proposed",
        nullable=False,
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    risk: Mapped[str] = mapped_column(
        String(30),
        default="medium",
        nullable=False,
    )
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    proposed_actions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )


class ExperimentRecord(Base, OperationalTimestampMixin):
    __tablename__ = "experiment_records"

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
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("campaign_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    primary_metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
    )
    control_configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    variant_configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
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


class CreativeAssetRecord(Base, OperationalTimestampMixin):
    __tablename__ = "creative_asset_records"

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
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        String(50),
        default="copy",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )


class ReportRecord(Base, OperationalTimestampMixin):
    __tablename__ = "report_records"

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
    report_type: Mapped[str] = mapped_column(
        String(50),
        default="daily",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="generated",
        nullable=False,
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class OrganizationSettingRecord(Base, OperationalTimestampMixin):
    __tablename__ = "organization_settings"
    __table_args__ = (
        Index(
            "ix_organization_settings_org_key", "organization_id", "key", unique=True
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class WebhookEventRecord(Base, OperationalTimestampMixin):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
