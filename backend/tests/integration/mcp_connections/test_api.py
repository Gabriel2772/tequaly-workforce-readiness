from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import AppUser
from app.auth.security import hash_password
from app.core.config import Settings
from app.db.base import Base
from app.decisions.models import AuditEvent
from app.main import create_app
from app.mcp_connections.service import McpConnectionService

PASSWORD = "TequalyDemo!2026"


@contextmanager
def _clients() -> Iterator[tuple[TestClient, TestClient, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        session.add_all(
            [
                AppUser(
                    username="alice",
                    email="alice@tequaly.local",
                    display_name="Alice",
                    password_hash=hash_password(PASSWORD),
                    role="planner",
                    active=True,
                ),
                AppUser(
                    username="bob",
                    email="bob@tequaly.local",
                    display_name="Bob",
                    password_hash=hash_password(PASSWORD),
                    role="planner",
                    active=True,
                ),
            ]
        )
        session.commit()
    settings = Settings(
        auth_required=True,
        environment="production",
        session_secret="test-secret-with-enough-entropy",
        secure_cookies=False,
    )
    app = create_app(session_factory=factory, settings=settings)
    try:
        with TestClient(app) as alice, TestClient(app) as bob:
            assert alice.post(
                "/auth/login", json={"username": "alice", "password": PASSWORD}
            ).status_code == 200
            assert bob.post(
                "/auth/login", json={"username": "bob", "password": PASSWORD}
            ).status_code == 200
            yield alice, bob, factory
    finally:
        engine.dispose()


def _payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "MCP Planejamento",
        "client_type": "claude",
        "endpoint_url": "https://MCP.EXAMPLE.COM:443/mcp?workspace=south",
        "transport": "streamable_http",
        "notes": "Configuração sem credenciais",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def test_connection_crud_is_scoped_to_the_authenticated_owner() -> None:
    with _clients() as (alice, bob, _factory):
        created = alice.post("/mcp-connections", json=_payload())

        assert created.status_code == 201
        connection_id = created.json()["id"]
        assert created.json()["endpoint_url"] == "https://mcp.example.com/mcp?workspace=south"
        assert [item["id"] for item in alice.get("/mcp-connections").json()] == [
            connection_id
        ]
        assert bob.get("/mcp-connections").json() == []
        assert (
            bob.patch(
                f"/mcp-connections/{connection_id}", json={"enabled": False}
            ).status_code
            == 404
        )
        assert bob.delete(f"/mcp-connections/{connection_id}").status_code == 404

        updated = alice.patch(
            f"/mcp-connections/{connection_id}",
            json={"name": "MCP Produção", "enabled": False},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "MCP Produção"
        assert updated.json()["enabled"] is False

        validated = alice.post(f"/mcp-connections/{connection_id}/validate")
        assert validated.status_code == 200
        assert validated.json()["valid"] is True
        assert validated.json()["normalized_endpoint_url"] == (
            "https://mcp.example.com/mcp?workspace=south"
        )

        deleted = alice.delete(f"/mcp-connections/{connection_id}")
        assert deleted.status_code == 204
        assert alice.get("/mcp-connections").json() == []


def test_missing_and_foreign_connections_use_the_same_not_found_response() -> None:
    with _clients() as (alice, bob, _factory):
        connection_id = alice.post("/mcp-connections", json=_payload()).json()["id"]
        foreign = bob.patch(f"/mcp-connections/{connection_id}", json={"enabled": False})
        missing = bob.patch(
            "/mcp-connections/00000000-0000-0000-0000-000000000000",
            json={"enabled": False},
        )

        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json()


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/mcp-connections", None),
        ("POST", "/mcp-connections", _payload()),
        ("GET", "/mcp-connections/catalog", None),
    ],
)
def test_routes_require_an_authenticated_twr_session(
    method: str, path: str, body: dict[str, Any] | None
) -> None:
    with _clients() as (_alice, _bob, factory):
        app = create_app(
            session_factory=factory,
            settings=Settings(
                auth_required=True,
                environment="production",
                session_secret="test-secret-with-enough-entropy",
            ),
        )
        with TestClient(app) as anonymous:
            response = anonymous.request(method, path, json=body)

        assert response.status_code == 401


def test_duplicate_name_for_the_same_owner_and_destination_returns_conflict() -> None:
    with _clients() as (alice, bob, _factory):
        assert alice.post("/mcp-connections", json=_payload()).status_code == 201

        duplicate = alice.post(
            "/mcp-connections", json=_payload(endpoint_url="https://other.example.com/mcp")
        )
        different_destination = alice.post(
            "/mcp-connections", json=_payload(client_type="chatgpt")
        )
        other_owner = bob.post("/mcp-connections", json=_payload())

        assert duplicate.status_code == 409
        assert different_destination.status_code == 201
        assert other_owner.status_code == 201


def test_unrelated_integrity_error_is_not_translated_to_duplicate_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = IntegrityError(
        "INSERT",
        {},
        RuntimeError("CHECK constraint failed: enabled_boolean"),
    )

    def fail_create(
        _service: McpConnectionService,
        _command: object,
    ) -> None:
        raise error

    monkeypatch.setattr(McpConnectionService, "create", fail_create)

    with _clients() as (alice, _bob, _factory), pytest.raises(IntegrityError) as raised:
        alice.post("/mcp-connections", json=_payload())

    assert raised.value is error


@pytest.mark.parametrize(
    "payload",
    [
        _payload(name=""),
        _payload(name="x" * 121),
        _payload(endpoint_url="x" * 2049),
        _payload(notes="x" * 1001),
        _payload(client_type="other"),
        _payload(transport="stdio"),
        _payload(user_id="00000000-0000-0000-0000-000000000000"),
        _payload(api_key="secret"),
    ],
)
def test_create_rejects_field_limit_enum_owner_and_secret_inputs(payload: dict[str, Any]) -> None:
    with _clients() as (alice, _bob, _factory):
        response = alice.post("/mcp-connections", json=payload)

        assert response.status_code == 422


def test_create_and_update_reject_unsafe_endpoint_urls() -> None:
    with _clients() as (alice, _bob, _factory):
        rejected = alice.post(
            "/mcp-connections",
            json=_payload(endpoint_url="https://mcp.example.com/mcp?apikey=secret"),
        )
        assert rejected.status_code == 422

        created = alice.post("/mcp-connections", json=_payload())
        update = alice.patch(
            f"/mcp-connections/{created.json()['id']}",
            json={"endpoint_url": "http://mcp.example.com/mcp"},
        )

        assert update.status_code == 422


def test_update_invalidates_only_connectivity_changes() -> None:
    with _clients() as (alice, _bob, _factory):
        created = alice.post("/mcp-connections", json=_payload())
        connection_id = created.json()["id"]
        validated = alice.post(f"/mcp-connections/{connection_id}/validate")
        validated_at = validated.json()["validated_at"]

        metadata_update = alice.patch(
            f"/mcp-connections/{connection_id}",
            json={"name": "MCP Produção", "notes": "Nota pública", "enabled": False},
        )

        assert metadata_update.status_code == 200
        assert metadata_update.json()["last_validated_at"].removesuffix("Z") == (
            validated_at.removesuffix("Z")
        )

        for payload in (
            {"endpoint_url": "https://other.example.com/mcp"},
            {"client_type": "chatgpt"},
            {"transport": "sse"},
        ):
            changed = alice.patch(
                f"/mcp-connections/{connection_id}",
                json=payload,
            )

            assert changed.status_code == 200
            assert changed.json()["last_validated_at"] is None
            assert (
                alice.post(f"/mcp-connections/{connection_id}/validate").status_code
                == 200
            )


def test_catalog_has_exactly_five_read_only_tools_and_precedes_uuid_route() -> None:
    with _clients() as (alice, _bob, _factory):
        response = alice.get("/mcp-connections/catalog")

        assert response.status_code == 200
        assert [item["name"] for item in response.json()] == [
            "get_readiness_overview",
            "get_operation",
            "get_employee_profile",
            "get_operational_fragility",
            "get_decision_run",
        ]
        assert {item["effect"] for item in response.json()} == {"read"}


def test_mutation_audit_contains_only_non_secret_connection_metadata() -> None:
    with _clients() as (alice, _bob, factory):
        created = alice.post("/mcp-connections", json=_payload())
        connection_id = created.json()["id"]
        alice.patch(f"/mcp-connections/{connection_id}", json={"enabled": False})
        alice.post(f"/mcp-connections/{connection_id}/validate")
        alice.delete(f"/mcp-connections/{connection_id}")

        with factory() as session:
            events = list(
                session.scalars(
                    select(AuditEvent)
                    .where(AuditEvent.aggregate_id == UUID(connection_id))
                    .order_by(AuditEvent.occurred_at)
                )
            )

        assert [event.event_type for event in events] == [
            "mcp_connection.created",
            "mcp_connection.updated",
            "mcp_connection.validated",
            "mcp_connection.deleted",
        ]
        assert {event.aggregate_type for event in events} == {"mcp_connection"}
        assert all(event.actor_id for event in events)
        assert all(
            set(event.payload) <= {"client_type", "transport", "enabled"}
            for event in events
        )
        assert all(
            "endpoint_url" not in event.payload and "notes" not in event.payload
            for event in events
        )
