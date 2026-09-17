"""add per-user MCP connection metadata

Revision ID: 0010_user_mcp_connections
Revises: 0010_mcp_oauth
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_user_mcp_connections"
down_revision: str | None = "0010_mcp_oauth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in (
        "mcp_refresh_tokens",
        "mcp_authorization_codes",
        "mcp_authorization_requests",
        "mcp_authorization_grants",
        "mcp_oauth_clients",
    ):
        op.drop_table(table_name, if_exists=True)

    op.create_table(
        "user_mcp_connections",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("client_type", sa.String(length=20), nullable=False),
        sa.Column("endpoint_url", sa.String(length=2048), nullable=False),
        sa.Column("transport", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "client_type",
            "name",
            name="uq_user_mcp_connection_name",
        ),
    )
    op.create_index(
        "ix_user_mcp_connections_owner",
        "user_mcp_connections",
        ["user_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_mcp_connections_owner", table_name="user_mcp_connections")
    op.drop_table("user_mcp_connections")
