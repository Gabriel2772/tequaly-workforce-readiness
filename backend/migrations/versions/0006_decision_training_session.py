"""link decision training actions to source sessions

Revision ID: 0006_decision_training_session
Revises: 0005_decision_run_snapshot
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_decision_training_session"
down_revision: str | None = "0005_decision_run_snapshot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("decision_training_actions") as batch_op:
        batch_op.add_column(sa.Column("training_session_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_decision_training_actions_training_session_id_training_sessions"),
            "training_sessions",
            ["training_session_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("decision_training_actions") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_decision_training_actions_training_session_id_training_sessions"),
            type_="foreignkey",
        )
        batch_op.drop_column("training_session_id")
