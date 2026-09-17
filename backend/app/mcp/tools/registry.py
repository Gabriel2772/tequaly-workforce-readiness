from typing import Any

from pydantic import ValidationError

from app.mcp.tools.types import ToolContext, ToolDefinition


class ToolRegistry:
    def __init__(self, definitions: list[ToolDefinition]) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        for definition in definitions:
            if definition.name in self._definitions:
                raise ValueError(f"duplicate_tool:{definition.name}")
            self._definitions[definition.name] = definition

    def execute(self, name: str, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        definition = self._definitions.get(name)
        if definition is None:
            raise ValueError(f"unknown_tool:{name}")
        try:
            command = definition.input_model.model_validate(arguments)
        except ValidationError as error:
            raise ValueError(f"invalid_arguments:{name}") from error
        return definition.handler(command, context)

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "effect": definition.effect,
                "input_schema": definition.input_model.model_json_schema(),
            }
            for definition in self._definitions.values()
        ]
