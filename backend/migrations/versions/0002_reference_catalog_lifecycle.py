"""add active lifecycle to remaining workforce catalogs

Revision ID: 0002_reference_catalog_lifecycle
Revises: 0001_core_schema
Create Date: 2026-08-11 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_reference_catalog_lifecycle"
down_revision: str | Sequence[str] | None = "0001_core_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "role_aliases",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "technical_competencies",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "operational_restrictions",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("operational_restrictions", "active")
    op.drop_column("technical_competencies", "active")
    op.drop_column("role_aliases", "active")
