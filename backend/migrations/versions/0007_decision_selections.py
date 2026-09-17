"""add auditable decision selections

Revision ID: 0007_decision_selections
Revises: 0006_decision_training_session
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_decision_selections"
down_revision: str | None = "0006_decision_training_session"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "decision_selections",
        sa.Column("decision_run_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_selection_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["decision_run_id"], ["decision_runs.id"]),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"]),
        sa.ForeignKeyConstraint(
            ["superseded_by_selection_id"], ["decision_selections.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_selections_decision_run_id",
        "decision_selections",
        ["decision_run_id"],
    )
    op.create_index(
        "ix_decision_selections_operation_id",
        "decision_selections",
        ["operation_id"],
    )
    op.create_index(
        "ix_decision_selections_operation_active",
        "decision_selections",
        ["operation_id", "superseded_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_decision_selections_operation_active", table_name="decision_selections"
    )
    op.drop_index("ix_decision_selections_operation_id", table_name="decision_selections")
    op.drop_index(
        "ix_decision_selections_decision_run_id", table_name="decision_selections"
    )
    op.drop_table("decision_selections")
