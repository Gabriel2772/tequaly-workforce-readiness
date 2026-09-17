from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

McpClientType = Literal["claude", "chatgpt"]
McpTransport = Literal["streamable_http", "sse"]


class McpConnectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    client_type: McpClientType
    endpoint_url: str = Field(min_length=1, max_length=2048)
    transport: McpTransport
    notes: str | None = Field(default=None, max_length=1000)
    enabled: bool = True

    @field_validator("name", "endpoint_url")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("field cannot be blank")
        return stripped

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class McpConnectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    client_type: McpClientType | None = None
    endpoint_url: str | None = Field(default=None, min_length=1, max_length=2048)
    transport: McpTransport | None = None
    notes: str | None = Field(default=None, max_length=1000)
    enabled: bool | None = None

    @field_validator("name", "endpoint_url")
    @classmethod
    def strip_optional_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("field cannot be blank")
        return stripped

    @field_validator("notes")
    @classmethod
    def strip_optional_notes(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_non_null_updates(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        non_nullable = self.model_fields_set - {"notes"}
        if any(getattr(self, field) is None for field in non_nullable):
            raise ValueError("updated fields cannot be null")
        return self


class McpConnectionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    client_type: McpClientType
    endpoint_url: str
    transport: McpTransport
    notes: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_validated_at: datetime | None


class McpConnectionValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    normalized_endpoint_url: str
    validated_at: datetime


class McpToolView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    effect: Literal["read"]
    input_schema: dict[str, object]
