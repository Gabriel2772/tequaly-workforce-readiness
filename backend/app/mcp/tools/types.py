from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

ToolEffect = Literal["read"]


@dataclass(frozen=True)
class ToolContext:
    session: Session | None
    actor_id: str


ToolHandler = Callable[[BaseModel, ToolContext], dict[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    effect: ToolEffect
    handler: ToolHandler
