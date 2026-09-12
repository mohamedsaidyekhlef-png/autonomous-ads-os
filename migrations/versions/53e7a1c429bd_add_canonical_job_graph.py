"""add canonical job graph

Revision ID: 53e7a1c429bd
Revises: 6eab3b9a41f2
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "53e7a1c429bd"
down_revision: Union[str, Sequence[str], None] = "6eab3b9a41f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canonical_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employer_name", sa.String(255), nullable=False),
        sa.Column("employer_domain", sa.String(255), nullable=False),
        sa.Column(
            "normalized_employer",
            sa.String(255),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column(
            "normalized_title",
            sa.String(500),
            nullable=False,
        ),
        sa.Column(
            "location_text",
            sa.String(500),
            nullable=True,
        ),
        sa.Column("team", sa.String(255), nullable=True),
        sa.Column(
            "employment_type",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "description_text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "description_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "dedupe_key",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "canonical_apply_url",
            sa.Text(),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dedupe_key",
            name="uq_canonical_jobs_dedupe_key",
        ),
    )
    op.create_index(
        "ix_canonical_jobs_employer_title",
        "canonical_jobs",
        ["normalized_employer", "normalized_title"],
    )
    op.create_index(
        "ix_canonical_jobs_status_last_seen",
        "canonical_jobs",
        ["status", "last_seen_at"],
    )

    op.create_table(
        "job_source_postings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column(
            "canonical_job_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column(
            "external_id",
            sa.String(500),
            nullable=False,
        ),
        sa.Column(
            "adapter_version",
            sa.String(100),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column(
            "location_text",
            sa.String(500),
            nullable=True,
        ),
        sa.Column("team", sa.String(255), nullable=True),
        sa.Column(
            "employment_type",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "description_text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "description_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("apply_url", sa.Text(), nullable=False),
        sa.Column(
            "source_updated_at",
            sa.String(100),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(
            ["canonical_job_id"],
            ["canonical_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "board_id",
            "external_id",
            name="uq_job_source_board_external",
        ),
    )
    op.create_index(
        "ix_job_source_canonical_active",
        "job_source_postings",
        ["canonical_job_id", "is_active"],
    )
    op.create_index(
        "ix_job_source_provider_external",
        "job_source_postings",
        ["provider", "external_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_job_source_provider_external",
        table_name="job_source_postings",
    )
    op.drop_index(
        "ix_job_source_canonical_active",
        table_name="job_source_postings",
    )
    op.drop_table("job_source_postings")

    op.drop_index(
        "ix_canonical_jobs_status_last_seen",
        table_name="canonical_jobs",
    )
    op.drop_index(
        "ix_canonical_jobs_employer_title",
        table_name="canonical_jobs",
    )
    op.drop_table("canonical_jobs")
