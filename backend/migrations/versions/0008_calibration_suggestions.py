"""add calibration suggestions

Revision ID: 0008_calibration_suggestions
Revises: 0007_decision_selections
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_calibration_suggestions"
down_revision: str | None = "0007_decision_selections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calibration_suggestions",
        sa.Column("parameter_name", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=160), nullable=False),
        sa.Column("current_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("proposed_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("confidence_basis", sa.String(length=80), nullable=False),
        sa.Column("interquartile_range", sa.Numeric(18, 6), nullable=False),
        sa.Column("rationale", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("applied_by", sa.String(length=120), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_parameter_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["applied_parameter_id"], ["calibration_parameters.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_calibration_suggestions_parameter_status",
        "calibration_suggestions",
        ["parameter_name", "category", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_calibration_suggestions_parameter_status",
        table_name="calibration_suggestions",
    )
    op.drop_table("calibration_suggestions")
