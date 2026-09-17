"""preserve the retired MCP OAuth revision as a compatibility bridge

Revision ID: 0010_mcp_oauth
Revises: 0009_import_batches
"""

from collections.abc import Sequence

revision: str = "0010_mcp_oauth"
down_revision: str | None = "0009_import_batches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Keep the published revision addressable without recreating retired tables."""


def downgrade() -> None:
    """The compatibility bridge has no schema of its own to remove."""
