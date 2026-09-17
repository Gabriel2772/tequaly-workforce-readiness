from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.main import create_app
from app.operations import models as operation_models  # noqa: F401
from app.workforce import models as workforce_models


def _client() -> tuple[TestClient, Engine, str]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with Session(engine) as session:
        family = workforce_models.RoleFamily(
            code="FAM-WRITE",
            name="Família Escrita",
            active=True,
        )
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="ROLE-WRITE",
            name="Cargo Escrita",
            active=True,
        )
        session.add(role)
        session.commit()
        role_id = str(role.id)
    return TestClient(create_app(session_factory=factory)), engine, role_id


def test_employee_create_patch_and_duplicate_contract() -> None:
    client, engine, role_id = _client()
    payload = {
        "employee_number": "EMP-API-001",
        "name": "Pessoa API",
        "canonical_role_id": role_id,
        "base_location": "Curitiba",
        "seniority_level": "pleno",
    }
    try:
        created = client.post("/employees", json=payload)
        assert created.status_code == 201
        duplicate = client.post("/employees", json=payload)
        patched = client.patch(
            f"/employees/{created.json()['id']}",
            json={"active": False, "seniority_level": "sênior"},
        )
        with Session(engine) as session:
            employee = session.scalar(
                select(workforce_models.Employee).where(
                    workforce_models.Employee.employee_number == "EMP-API-001"
                )
            )
    finally:
        engine.dispose()

    assert duplicate.status_code == 409
    assert patched.status_code == 200
    assert employee is not None
    assert employee.active is False
    assert employee.seniority_level == "sênior"


def test_viewer_write_is_rejected_with_stable_code_and_no_side_effect() -> None:
    client, engine, role_id = _client()
    try:
        response = client.post(
            "/employees",
            headers={"X-TWR-Actor": "viewer@example.com", "X-TWR-Role": "viewer"},
            json={
                "employee_number": "EMP-DENIED-001",
                "name": "Pessoa sem permissão",
                "canonical_role_id": role_id,
                "base_location": "Curitiba",
                "seniority_level": "pleno",
            },
        )
        qualification_response = client.post(
            "/qualifications",
            headers={"X-TWR-Actor": "viewer@example.com", "X-TWR-Role": "viewer"},
            json={
                "code": "QLF-DENIED",
                "name": "Qualificação negada",
                "category": "segurança",
            },
        )
        with Session(engine) as session:
            employee_count = session.scalar(
                select(func.count()).select_from(workforce_models.Employee)
            )
            qualification_count = session.scalar(
                select(func.count()).select_from(workforce_models.Qualification)
            )
    finally:
        engine.dispose()

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "write_forbidden"
    assert qualification_response.status_code == 403
    assert qualification_response.json()["detail"]["code"] == "write_forbidden"
    assert employee_count == 0
    assert qualification_count == 0


def test_qualification_catalog_create_list_patch_and_duplicate_contract() -> None:
    client, engine, _role_id = _client()
    payload = {
        "code": "QLF-API-001",
        "name": "Qualificação API",
        "category": "segurança",
        "validity_days": 730,
    }
    try:
        created = client.post("/qualifications", json=payload)
        assert created.status_code == 201
        duplicate = client.post("/qualifications", json=payload)
        patched = client.patch(
            f"/qualifications/{created.json()['id']}",
            json={"name": "Qualificação API Atualizada", "validity_days": 365},
        )
        listed = client.get("/qualifications?page=1&page_size=25")
    finally:
        engine.dispose()

    assert duplicate.status_code == 409
    assert patched.status_code == 200
    assert listed.status_code == 200
    assert listed.json()["page"] == 1
    assert listed.json()["page_size"] == 25
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["name"] == "Qualificação API Atualizada"


def test_reference_catalogs_support_paginated_active_lifecycle() -> None:
    client, engine, role_id = _client()
    with Session(engine) as session:
        family_id = str(session.scalar(select(workforce_models.RoleFamily.id)))

    qualification = client.post(
        "/qualifications",
        json={
            "code": "QLF-TRAINING-API",
            "name": "Qualificação do treinamento",
            "category": "técnica",
        },
    )
    assert qualification.status_code == 201
    catalog_payloads = (
        (
            "/roles",
            {
                "family_id": family_id,
                "code": "ROLE-API-002",
                "name": "Cargo API 2",
            },
            "ROLE-API-002",
        ),
        (
            "/role-aliases",
            {
                "role_id": role_id,
                "source_title": "Cargo de Campo",
                "normalized_title": "cargo de campo",
            },
            "cargo de campo",
        ),
        (
            "/authorizations",
            {
                "code": "AUT-API-001",
                "name": "Autorização API",
                "scope_type": "cliente",
            },
            "AUT-API-001",
        ),
        (
            "/training-catalog",
            {
                "code": "TRN-API-001",
                "name": "Treinamento API",
                "qualification_id": qualification.json()["id"],
                "duration_minutes": 480,
                "cost_cents": 25_000,
            },
            "TRN-API-001",
        ),
        (
            "/competencies",
            {"code": "CMP-API-001", "name": "Competência API", "scale_max": 5},
            "CMP-API-001",
        ),
        (
            "/restrictions",
            {
                "code": "RST-API-001",
                "name": "Restrição API",
                "hard_constraint": True,
            },
            "RST-API-001",
        ),
    )
    try:
        results = []
        for route, payload, natural_key in catalog_payloads:
            created = client.post(route, json=payload)
            patched = client.patch(f"{route}/{created.json()['id']}", json={"active": False})
            listed = client.get(f"{route}?page=1&page_size=100")
            item = next(
                candidate
                for candidate in listed.json()["items"]
                if natural_key in {candidate.get("code"), candidate.get("normalized_title")}
            )
            results.append((created.status_code, patched.status_code, item["active"]))
    finally:
        engine.dispose()

    assert results == [(201, 200, False)] * 6


def test_employee_profile_subresources_are_created_transactionally() -> None:
    client, engine, role_id = _client()
    with Session(engine) as session:
        qualification = workforce_models.Qualification(
            code="QLF-LINK",
            name="Qualificação Vínculo",
            category="segurança",
            validity_days=730,
            active=True,
        )
        authorization = workforce_models.Authorization(
            code="AUT-LINK",
            name="Autorização Vínculo",
            scope_type="cliente",
            active=True,
        )
        competency = workforce_models.TechnicalCompetency(
            code="CMP-LINK",
            name="Competência Vínculo",
            scale_max=5,
        )
        restriction = workforce_models.OperationalRestriction(
            code="RST-LINK",
            name="Restrição Vínculo",
            hard_constraint=True,
        )
        operation = operation_models.Operation(
            code="OPS-LINK",
            name="Operação Vínculo",
            client_name="Cliente Vínculo",
            base_location="Curitiba",
            starts_at=datetime(2026, 10, 1, tzinfo=UTC),
            ends_at=datetime(2026, 11, 1, tzinfo=UTC),
            status="planning",
            budget_cents=1_000_000,
        )
        session.add_all((qualification, authorization, competency, restriction, operation))
        session.commit()
        reference_ids = {
            "qualification": str(qualification.id),
            "authorization": str(authorization.id),
            "competency": str(competency.id),
            "restriction": str(restriction.id),
            "operation": str(operation.id),
        }

    employee = client.post(
        "/employees",
        json={
            "employee_number": "EMP-LINK-001",
            "name": "Pessoa Vínculos",
            "canonical_role_id": role_id,
            "base_location": "Curitiba",
            "seniority_level": "pleno",
        },
    )
    employee_id = employee.json()["id"]
    payloads = (
        (
            "qualifications",
            {
                "qualification_id": reference_ids["qualification"],
                "issued_on": "2026-01-01",
                "expires_on": "2027-12-31",
            },
        ),
        (
            "authorizations",
            {
                "authorization_id": reference_ids["authorization"],
                "scope_value": "Cliente Vínculo",
                "issued_on": "2026-01-01",
                "expires_on": "2027-01-01",
            },
        ),
        (
            "availability",
            {
                "starts_at": "2026-10-01T00:00:00Z",
                "ends_at": "2026-12-01T00:00:00Z",
                "status": "available",
            },
        ),
        (
            "assignments",
            {
                "operation_id": reference_ids["operation"],
                "starts_at": "2026-10-01T00:00:00Z",
                "ends_at": "2026-11-01T00:00:00Z",
                "status": "planned",
            },
        ),
        (
            "costs",
            {
                "currency": "BRL",
                "hourly_cost_cents": 12_000,
                "travel_cost_cents": 25_000,
                "effective_from": "2026-08-10",
            },
        ),
        (
            "competencies",
            {
                "competency_id": reference_ids["competency"],
                "level": 4,
                "assessed_on": "2026-08-10",
            },
        ),
        (
            "restrictions",
            {
                "restriction_id": reference_ids["restriction"],
                "scope_value": "turno_noturno",
            },
        ),
    )
    try:
        responses = [
            client.post(f"/employees/{employee_id}/{path}", json=payload)
            for path, payload in payloads
        ]
        update_payloads = (
            ("qualifications", {"expires_on": "2028-12-31"}),
            ("authorizations", {"scope_value": "Cliente Atualizado"}),
            ("availability", {"status": "reserved"}),
            ("assignments", {"status": "confirmed"}),
            ("costs", {"hourly_cost_cents": 13_500}),
            ("competencies", {"level": 5}),
            ("restrictions", {"notes": "Revisão ocupacional pendente"}),
        )
        patched = [
            client.patch(
                f"/employees/{employee_id}/{path}/{created.json()['id']}",
                json=update_payload,
            )
            for (path, update_payload), created in zip(update_payloads, responses, strict=True)
        ]
        with Session(engine) as session:
            counts = [
                session.scalar(select(func.count()).select_from(model))
                for model in (
                    workforce_models.EmployeeQualification,
                    workforce_models.EmployeeAuthorization,
                    workforce_models.EmployeeAvailability,
                    workforce_models.EmployeeAssignment,
                    workforce_models.EmployeeCostProfile,
                    workforce_models.EmployeeCompetency,
                    workforce_models.EmployeeOperationalRestriction,
                )
            ]
            updated_values = (
                session.scalar(select(workforce_models.EmployeeQualification)).expires_on,
                session.scalar(select(workforce_models.EmployeeAuthorization)).scope_value,
                session.scalar(select(workforce_models.EmployeeAvailability)).status,
                session.scalar(select(workforce_models.EmployeeAssignment)).status,
                session.scalar(select(workforce_models.EmployeeCostProfile)).hourly_cost_cents,
                session.scalar(select(workforce_models.EmployeeCompetency)).level,
                session.scalar(select(workforce_models.EmployeeOperationalRestriction)).notes,
            )
    finally:
        engine.dispose()

    assert [response.status_code for response in responses] == [201] * 7
    assert [response.status_code for response in patched] == [200] * 7
    assert counts == [1] * 7
    assert tuple(str(value) for value in updated_values) == (
        "2028-12-31",
        "Cliente Atualizado",
        "reserved",
        "confirmed",
        "13500",
        "5",
        "Revisão ocupacional pendente",
    )
