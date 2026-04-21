"""initial_schema

Revision ID: 9e97ad218f7c
Revises:
Create Date: 2026-04-20 11:20:20.975534
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9e97ad218f7c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("seniority", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cleaned_description", sa.Text(), nullable=True),
        sa.Column("detected_skills", sa.Text(), nullable=True),
        sa.Column("date_posted", sa.Date(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("processing_status", sa.String(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.Column("last_processed_at", sa.DateTime(), nullable=True),
        sa.Column("source_hash", sa.String(), nullable=True),
        sa.Column("skills_extracted_at", sa.DateTime(), nullable=True),
        sa.Column("embedded_at", sa.DateTime(), nullable=True),
        sa.Column("chunked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index(op.f("ix_jobs_source_hash"), "jobs", ["source_hash"], unique=False)

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pipeline_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=True),
        sa.Column("input_rows", sa.Integer(), nullable=True),
        sa.Column("output_rows", sa.Integer(), nullable=True),
        sa.Column("inserted_rows", sa.Integer(), nullable=True),
        sa.Column("updated_rows", sa.Integer(), nullable=True),
        sa.Column("skipped_rows", sa.Integer(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_runs_id"), "pipeline_runs", ["id"], unique=False)
    op.create_index(
        op.f("ix_pipeline_runs_pipeline_name"),
        "pipeline_runs",
        ["pipeline_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pipeline_runs_status"),
        "pipeline_runs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_runs_status"), table_name="pipeline_runs")
    op.drop_index(op.f("ix_pipeline_runs_pipeline_name"), table_name="pipeline_runs")
    op.drop_index(op.f("ix_pipeline_runs_id"), table_name="pipeline_runs")
    op.drop_table("pipeline_runs")

    op.drop_index(op.f("ix_jobs_source_hash"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_id"), table_name="jobs")
    op.drop_table("jobs")