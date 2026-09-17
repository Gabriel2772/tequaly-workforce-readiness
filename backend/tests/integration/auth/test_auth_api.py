from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import AppUser
from app.auth.security import hash_password
from app.core.config import Settings
from app.db.base import Base
from app.main import create_app


def _client(*, auth_required: bool = True) -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        session.add_all(
            [
                AppUser(
                    username="planejador.demo",
                    email="planejador.demo@tequaly.local",
                    display_name="Planejador de demonstração",
                    password_hash=hash_password("TequalyDemo!2026"),
                    role="planner",
                    active=True,
                ),
                AppUser(
                    username="admin.demo",
                    email="admin.demo@tequaly.local",
                    display_name="Administrador de demonstração",
                    password_hash=hash_password("TequalyDemo!2026"),
                    role="admin",
                    active=True,
                ),
            ]
        )
        session.commit()
    settings = Settings(
        auth_required=auth_required,
        session_secret="test-secret-with-enough-entropy",
        secure_cookies=False,
    )
    return TestClient(create_app(session_factory=factory, settings=settings)), factory


def test_login_sets_http_only_session_and_me_returns_safe_profile() -> None:
    client, factory = _client()
    try:
        response = client.post(
            "/auth/login",
            json={"username": "planejador.demo", "password": "TequalyDemo!2026"},
        )
        current = client.get("/auth/me")
    finally:
        factory.kw["bind"].dispose()

    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert response.json()["role"] == "planner"
    assert "password_hash" not in response.json()
    assert current.status_code == 200
    assert current.json()["display_name"] == "Planejador de demonstração"


def test_invalid_credentials_use_a_generic_error() -> None:
    client, factory = _client()
    try:
        unknown = client.post(
            "/auth/login", json={"username": "desconhecido", "password": "incorreta"}
        )
        wrong = client.post("/auth/login", json={"username": "admin.demo", "password": "incorreta"})
    finally:
        factory.kw["bind"].dispose()

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_strict_mode_ignores_spoofable_actor_headers() -> None:
    client, factory = _client()
    try:
        response = client.post(
            "/imports/preview",
            json={
                "contract": "employees",
                "filename": "employees.csv",
                "content_base64": "TWF0csOtY3VsYSxOb21lCg==",
            },
            headers={"X-TWR-Actor": "spoofed", "X-TWR-Role": "admin"},
        )
    finally:
        factory.kw["bind"].dispose()

    assert response.status_code == 401


def test_admin_session_can_reach_admin_only_import_endpoint() -> None:
    client, factory = _client()
    try:
        client.post(
            "/auth/login",
            json={"username": "admin.demo", "password": "TequalyDemo!2026"},
        )
        response = client.post(
            "/imports/preview",
            json={
                "contract": "employees",
                "filename": "employees.csv",
                "content_base64": "TWF0csOtY3VsYSxOb21lCg==",
            },
        )
    finally:
        factory.kw["bind"].dispose()

    assert response.status_code != 401
    assert response.status_code != 403
