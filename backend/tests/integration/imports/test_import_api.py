import base64

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.main import create_app
from app.workforce.models import Employee

ADMIN_HEADERS = {"X-TWR-Actor": "admin@example.com", "X-TWR-Role": "admin"}


def _client() -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()
    return TestClient(create_app(session_factory=factory)), factory


def _payload(csv_text: str) -> dict[str, str]:
    return {
        "contract": "employees",
        "filename": "colaboradores.csv",
        "content_base64": base64.b64encode(csv_text.encode()).decode(),
    }


def test_preview_reports_row_errors_without_persisting_domain_data() -> None:
    client, factory = _client()
    before = 0
    with factory() as session:
        before = session.scalar(select(func.count()).select_from(Employee)) or 0

    response = client.post(
        "/imports/preview",
        json=_payload(
            "Matr�cula,Nome,Cargo,Base,N�vel,Admiss�o\n"
            "IMP-001,Pessoa Importada,CARGO-INEXISTENTE,Curitiba,pleno,24/08/2026\n"
        ),
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 201
    assert response.json()["invalid_rows"] == 1
    assert response.json()["errors"][0]["code"] == "unknown_role"
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Employee)) == before


def test_valid_preview_commits_once_and_preserves_unicode() -> None:
    client, factory = _client()
    with factory() as session:
        role_code = session.scalar(select(Employee).limit(1)).canonical_role_id
        from app.workforce.models import Role

        canonical_code = session.get(Role, role_code).code
    preview = client.post(
        "/imports/preview",
        json=_payload(
            "Matr�cula,Nome,Email,Cargo,Base,N�vel,Admiss�o,Ativo\n"
            "IMP-001,Jo�o da Concei��o,joao.importado@example.com,"
            f"{canonical_code},Curitiba,pleno,24/08/2026,sim\n"
        ),
        headers=ADMIN_HEADERS,
    )
    assert preview.status_code == 201
    assert preview.json()["valid_rows"] == 1
    assert preview.json()["invalid_rows"] == 0

    command = {"preview_token": preview.json()["token"], "confirmed": True}
    committed = client.post("/imports/commit", json=command, headers=ADMIN_HEADERS)
    repeated = client.post("/imports/commit", json=command, headers=ADMIN_HEADERS)

    assert committed.status_code == 200
    assert committed.json()["created"] == 1
    assert repeated.status_code == 200
    assert repeated.json()["idempotent"] is True
    with factory() as session:
        employee = session.scalar(select(Employee).where(Employee.employee_number == "IMP-001"))
        assert employee is not None
        assert employee.name == "Jo�o da Concei��o"


def test_import_requires_admin_role() -> None:
    client, _ = _client()

    response = client.post(
        "/imports/preview",
        json=_payload("Matr�cula,Nome\nIMP-001,Pessoa\n"),
        headers={"X-TWR-Role": "planner"},
    )

    assert response.status_code == 403
