from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.models import AppUser
from app.db.base import Base
from app.decisions.models import AuditEvent
from app.mcp_connections.models import UserMcpConnection
from app.mcp_connections.schemas import McpConnectionCreate, McpConnectionUpdate
from app.mcp_connections.service import McpConnectionService


@contextmanager
def _service() -> Iterator[tuple[McpConnectionService, Session]]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(
        engine,
        tables=[
            cast(Table, AppUser.__table__),
            cast(Table, UserMcpConnection.__table__),
            cast(Table, AuditEvent.__table__),
        ],
    )
    with Session(engine) as session:
        user_id = uuid4()
        yield (
            McpConnectionService(
                session,
                user_id=user_id,
                actor_id=str(user_id),
                environment="production",
            ),
            session,
        )
    engine.dispose()


def _validated_connection(
    service: McpConnectionService,
) -> tuple[UserMcpConnection, datetime]:
    connection = service.create(
        McpConnectionCreate(
            name="MCP Planejamento",
            client_type="claude",
            endpoint_url="https://mcp.example.com/mcp",
            transport="streamable_http",
            notes="Sem segredos",
            enabled=True,
        )
    )
    validated_at = service.validate(connection.id).validated_at
    return connection, validated_at


@pytest.mark.parametrize(
    "command",
    [
        McpConnectionUpdate(endpoint_url="https://other.example.com/mcp"),
        McpConnectionUpdate(client_type="chatgpt"),
        McpConnectionUpdate(transport="sse"),
    ],
)
def test_connectivity_changes_clear_last_validation(
    command: McpConnectionUpdate,
) -> None:
    with _service() as (service, _session):
        connection, _validated_at = _validated_connection(service)

        updated = service.update(connection.id, command)

        assert updated.last_validated_at is None


def test_metadata_only_changes_preserve_last_validation() -> None:
    with _service() as (service, _session):
        connection, validated_at = _validated_connection(service)

        updated = service.update(
            connection.id,
            McpConnectionUpdate(
                name="MCP Produ��o",
                notes="Nota p�blica",
                enabled=False,
            ),
        )

        assert updated.last_validated_at == validated_at
