"""add ATS coverage index

Revision ID: 6eab3b9a41f2
Revises: 509d6b3dbead
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "6eab3b9a41f2"
down_revision: Union[str, Sequence[str], None] = "509d6b3dbead"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ats_boards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "discovered_by_organization_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column("employer_name", sa.String(length=255), nullable=False),
        sa.Column("employer_domain", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("board_token", sa.String(length=500), nullable=False),
        sa.Column("board_url", sa.Text(), nullable=False),
        sa.Column("careers_url", sa.Text(), nullable=True),
        sa.Column("source_method", sa.String(length=30), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("posting_count", sa.Integer(), nullable=False),
        sa.Column("schema_hash", sa.String(length=128), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_successful_fetch_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "next_check_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("board_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["discovered_by_organization_id"],
            ["organizations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "board_token",
            name="uq_ats_boards_provider_token",
        ),
    )
    op.create_index(
        "ix_ats_boards_discovered_by_organization_id",
        "ats_boards",
        ["discovered_by_organization_id"],
    )
    op.create_index(
        "ix_ats_boards_employer_domain",
        "ats_boards",
        ["employer_domain"],
    )
    op.create_index(
        "ix_ats_boards_provider",
        "ats_boards",
        ["provider"],
    )
    op.create_index(
        "ix_ats_boards_state",
        "ats_boards",
        ["state"],
    )
    op.create_index(
        "ix_ats_boards_state_next_check",
        "ats_boards",
        ["state", "next_check_at"],
    )

    op.create_table(
        "ats_board_health_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("successful", sa.Boolean(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("posting_count", sa.Integer(), nullable=True),
        sa.Column("schema_hash", sa.String(length=128), nullable=True),
        sa.Column("schema_changed", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["ats_boards.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ats_board_health_checks_board_id",
        "ats_board_health_checks",
        ["board_id"],
    )
    op.create_index(
        "ix_ats_health_board_checked",
        "ats_board_health_checks",
        ["board_id", "checked_at"],
    )

    op.create_table(
        "ats_drift_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "previous_schema_hash",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "observed_schema_hash",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["ats_boards.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ats_drift_alerts_board_id",
        "ats_drift_alerts",
        ["board_id"],
    )
    op.create_index(
        "ix_ats_drift_status_detected",
        "ats_drift_alerts",
        ["status", "detected_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ats_drift_status_detected",
        table_name="ats_drift_alerts",
    )
    op.drop_index(
        "ix_ats_drift_alerts_board_id",
        table_name="ats_drift_alerts",
    )
    op.drop_table("ats_drift_alerts")

    op.drop_index(
        "ix_ats_health_board_checked",
        table_name="ats_board_health_checks",
    )
    op.drop_index(
        "ix_ats_board_health_checks_board_id",
        table_name="ats_board_health_checks",
    )
    op.drop_table("ats_board_health_checks")

    op.drop_index(
        "ix_ats_boards_state_next_check",
        table_name="ats_boards",
    )
    op.drop_index("ix_ats_boards_state", table_name="ats_boards")
    op.drop_index("ix_ats_boards_provider", table_name="ats_boards")
    op.drop_index(
        "ix_ats_boards_employer_domain",
        table_name="ats_boards",
    )
    op.drop_index(
        "ix_ats_boards_discovered_by_organization_id",
        table_name="ats_boards",
    )
    op.drop_table("ats_boards")
