"""add durable expert review runs

Revision ID: 8f29c4a7d103
Revises: 509d6b3dbead
Create Date: 2026-09-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8f29c4a7d103"
down_revision: Union[str, Sequence[str], None] = "509d6b3dbead"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expert_review_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("analysis_engine", sa.String(length=50), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("evidence_data", sa.JSON(), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=True),
        sa.Column("validation_data", sa.JSON(), nullable=True),
        sa.Column("report_hash", sa.String(length=64), nullable=True),
        sa.Column("rubric_version", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_expert_review_runs_org_idempotency",
        ),
    )
    op.create_index(
        "ix_expert_review_runs_organization_id",
        "expert_review_runs",
        ["organization_id"],
    )
    op.create_index(
        "ix_expert_review_runs_org_status",
        "expert_review_runs",
        ["organization_id", "status"],
    )

    op.create_table(
        "expert_human_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_identity", sa.String(length=200), nullable=False),
        sa.Column("reviewer_role", sa.String(length=200), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.Column("report_hash", sa.String(length=64), nullable=False),
        sa.Column("rubric_version", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["expert_review_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            name="uq_expert_human_reviews_run",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_expert_human_reviews_org_idempotency",
        ),
    )
    op.create_index(
        "ix_expert_human_reviews_run_id",
        "expert_human_reviews",
        ["run_id"],
    )
    op.create_index(
        "ix_expert_human_reviews_organization_id",
        "expert_human_reviews",
        ["organization_id"],
    )
    op.create_index(
        "ix_expert_human_reviews_org_decision",
        "expert_human_reviews",
        ["organization_id", "decision"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_expert_human_reviews_org_decision",
        table_name="expert_human_reviews",
    )
    op.drop_index(
        "ix_expert_human_reviews_organization_id",
        table_name="expert_human_reviews",
    )
    op.drop_index(
        "ix_expert_human_reviews_run_id",
        table_name="expert_human_reviews",
    )
    op.drop_table("expert_human_reviews")

    op.drop_index(
        "ix_expert_review_runs_org_status",
        table_name="expert_review_runs",
    )
    op.drop_index(
        "ix_expert_review_runs_organization_id",
        table_name="expert_review_runs",
    )
    op.drop_table("expert_review_runs")
