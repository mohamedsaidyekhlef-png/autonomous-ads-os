"""shadow beta durable commands and Whop events

Revision ID: 509d6b3dbead
Revises: 304249570cd6
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "509d6b3dbead"
down_revision: Union[str, Sequence[str], None] = "304249570cd6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("request_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("agent_runs", sa.Column("result_data", sa.JSON(), nullable=True))
    op.add_column("agent_runs", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.create_index("ix_agent_runs_org_idempotency", "agent_runs", ["organization_id", "idempotency_key"], unique=True)
    op.create_table(
        "organization_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_settings_org_key", "organization_settings", ["organization_id", "key"], unique=True)
    op.create_index(op.f("ix_organization_settings_organization_id"), "organization_settings", ["organization_id"])
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_index(op.f("ix_organization_settings_organization_id"), table_name="organization_settings")
    op.drop_index("ix_organization_settings_org_key", table_name="organization_settings")
    op.drop_table("organization_settings")
    op.drop_index("ix_agent_runs_org_idempotency", table_name="agent_runs")
    op.drop_column("agent_runs", "idempotency_key")
    op.drop_column("agent_runs", "result_data")
    op.drop_column("agent_runs", "request_data")
