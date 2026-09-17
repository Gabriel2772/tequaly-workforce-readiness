from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.main import create_app
from app.operations import models as operation_models  # noqa: F401
from app.workforce import models as workforce_models  # noqa: F401


def _client() -> tuple[TestClient, Engine]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with Session(engine) as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()
    return TestClient(create_app(session_factory=factory)), engine


def test_employee_list_is_paginated_and_filterable() -> None:
    client, engine = _client()
    try:
        response = client.get("/employees", params={"page": 1, "page_size": 5})
        filtered = client.get("/employees", params={"query": "SYN-00001"})
    finally:
        engine.dispose()

    assert response.status_code == 200
    assert response.json()["total"] == 20
    assert len(response.json()["items"]) == 5
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


def test_employee_profile_preserves_the_canonical_shape() -> None:
    client, engine = _client()
    try:
        list_response = client.get("/employees", params={"page_size": 1})
        employee_id = UUID(list_response.json()["items"][0]["id"])
        response = client.get(f"/employees/{employee_id}/profile")
    finally:
        engine.dispose()

    assert response.status_code == 200
    assert list(response.json())[:3] == [
        "cargo_funcao_principal",
        "nome",
        "qualificacoes",
    ]
    assert response.json()["nome"].startswith("Colaborador Sintético ")


def test_unknown_employee_profile_returns_404() -> None:
    client, engine = _client()
    try:
        response = client.get("/employees/00000000-0000-0000-0000-000000000001/profile")
    finally:
        engine.dispose()

    assert response.status_code == 404
