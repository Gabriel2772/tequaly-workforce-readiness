"""add eligibility run metrics and structured result facts

Revision ID: 0004_eligibility_run_metrics
Revises: 0003_operation_mobilization_deadline
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_eligibility_run_metrics"
down_revision: str | None = "0003_operation_mobilization_deadline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "eligibility_runs",
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "eligibility_runs",
        sa.Column("evaluated_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "eligibility_runs",
        sa.Column("eligible_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "eligibility_runs",
        sa.Column("trainable_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "eligibility_runs",
        sa.Column("ineligible_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("eligibility_runs", sa.Column("runtime_ms", sa.Integer(), nullable=True))
    op.add_column(
        "eligibility_results",
        sa.Column("reasons", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "eligibility_results",
        sa.Column("required_training_ids", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("eligibility_results", "required_training_ids")
    op.drop_column("eligibility_results", "reasons")
    op.drop_column("eligibility_runs", "runtime_ms")
    op.drop_column("eligibility_runs", "ineligible_count")
    op.drop_column("eligibility_runs", "trainable_count")
    op.drop_column("eligibility_runs", "eligible_count")
    op.drop_column("eligibility_runs", "evaluated_count")
    op.drop_column("eligibility_runs", "candidate_count")
