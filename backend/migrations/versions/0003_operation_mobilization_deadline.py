"""add operation mobilization deadline

Revision ID: 0003_operation_mobilization_deadline
Revises: 0002_reference_catalog_lifecycle
Create Date: 2026-08-11 20:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_operation_mobilization_deadline"
down_revision: str | Sequence[str] | None = "0002_reference_catalog_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "operations",
        sa.Column("mobilization_deadline", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("operations", "mobilization_deadline")
