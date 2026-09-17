"""add decision candidate snapshot and training duration

Revision ID: 0005_decision_run_snapshot
Revises: 0004_eligibility_run_metrics
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_decision_run_snapshot"
down_revision: str | None = "0004_eligibility_run_metrics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "decision_runs",
        sa.Column("candidate_snapshot", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "decision_training_actions",
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("decision_training_actions", "duration_minutes")
    op.drop_column("decision_runs", "candidate_snapshot")
