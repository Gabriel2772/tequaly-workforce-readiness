from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict

from app.mcp.tools.registry import ToolRegistry
from app.mcp.tools.types import ToolContext, ToolDefinition


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")
    horizon_days: int = 180


def test_registry_rejects_duplicates_unknown_tools_and_sql_arguments() -> None:
    """Catch a registry that accepts ambiguous tool names or unvalidated input."""
    definition = ToolDefinition(
        name="overview",
        description="Resumo",
        input_model=Input,
        effect="read",
        handler=lambda command, _context: {"horizon": command.horizon_days},
    )
    registry = ToolRegistry([definition])

    with pytest.raises(ValueError, match="duplicate_tool"):
        ToolRegistry([definition, definition])
    with pytest.raises(ValueError, match="unknown_tool"):
        registry.execute("missing", {}, ToolContext(session=None, actor_id="viewer"))
    with pytest.raises(ValueError, match="invalid_arguments"):
        registry.execute(
            "overview",
            {"horizon_days": 90, "sql": "select *"},
            ToolContext(session=None, actor_id="viewer"),
        )


def test_catalog_exposes_only_read_effects() -> None:
    """Catch a catalog whose consumer-visible effect is no longer read-only."""
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="overview",
                description="Resumo",
                input_model=Input,
                effect="read",
                handler=lambda command, _context: {"horizon": command.horizon_days},
            )
        ]
    )

    catalog = registry.catalog()
    effect: Literal["read"] = catalog[0]["effect"]
    assert effect == "read"
