from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models
from app.main import create_app
from app.operations import models as operation_models
from app.workforce import models as workforce_models


def test_operation_create_persists_demands_requirements_and_audit_atomically() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="FAM-OPS", name="Família Operações", active=True)
        session.add(family)
        session.flush()
        primary_role = workforce_models.Role(
            family_id=family.id, code="ROLE-OPS-1", name="Cargo Operação 1", active=True
        )
        compatible_role = workforce_models.Role(
            family_id=family.id, code="ROLE-OPS-2", name="Cargo Operação 2", active=True
        )
        qualification = workforce_models.Qualification(
            code="QLF-OPS",
            name="Qualificação Operacional",
            category="segurança",
            active=True,
        )
        session.add_all((primary_role, compatible_role, qualification))
        session.commit()
        ids = {
            "primary_role": str(primary_role.id),
            "compatible_role": str(compatible_role.id),
            "qualification": str(qualification.id),
        }

    client = TestClient(create_app(session_factory=factory))
    try:
        created = client.post(
            "/operations",
            headers={"X-TWR-Actor": "planner.ops@example.com", "X-TWR-Role": "planner"},
            json={
                "code": "OPS-API-001",
                "name": "Parada programada API",
                "client_name": "Cliente API",
                "base_location": "Curitiba",
                "starts_at": "2026-10-01T08:00:00Z",
                "ends_at": "2026-10-31T18:00:00Z",
                "mobilization_deadline": "2026-09-20T18:00:00Z",
                "status": "planning",
                "demands": [
                    {
                        "role_id": ids["primary_role"],
                        "quantity": 4,
                        "shift_code": "day",
                        "compatible_role_ids": [ids["compatible_role"]],
                    }
                ],
                "requirements": [
                    {
                        "code": "REQ-NR10",
                        "name": "NR-10 válida até o fim",
                        "requirement_type": "qualification",
                        "role_id": ids["primary_role"],
                        "qualification_ids": [ids["qualification"]],
                        "allows_training": True,
                        "payload": {"valid_through_operation_end": True},
                    }
                ],
            },
        )
        patched = client.patch(
            f"/operations/{created.json()['id']}",
            headers={"X-TWR-Actor": "planner.ops@example.com", "X-TWR-Role": "planner"},
            json={"status": "approved", "budget_cents": 2_500_000},
        )
        listed = client.get("/operations?page=1&page_size=25")
        detail = client.get(f"/operations/{created.json()['id']}")
        demand_patch = client.patch(
            f"/operations/{created.json()['id']}/demands/{detail.json()['demands'][0]['id']}",
            headers={"X-TWR-Actor": "planner.ops@example.com", "X-TWR-Role": "planner"},
            json={"quantity": 5, "priority": 10},
        )
        requirement_patch = client.patch(
            f"/operations/{created.json()['id']}/requirements/{detail.json()['requirements'][0]['id']}",
            headers={"X-TWR-Actor": "planner.ops@example.com", "X-TWR-Role": "planner"},
            json={"payload": {"valid_through_operation_end": True, "minimum_experience_years": 3}},
        )
        updated_detail = client.get(f"/operations/{created.json()['id']}")
        requirements = client.get(f"/operations/{created.json()['id']}/requirements")
        with Session(engine) as session:
            counts = {
                "operations": session.scalar(
                    select(func.count()).select_from(operation_models.Operation)
                ),
                "demands": session.scalar(
                    select(func.count()).select_from(operation_models.OperationRoleDemand)
                ),
                "compatible": session.scalar(
                    select(func.count()).select_from(operation_models.OperationRoleCompatibleRole)
                ),
                "requirements": session.scalar(
                    select(func.count()).select_from(operation_models.OperationRequirement)
                ),
                "maps": session.scalar(
                    select(func.count()).select_from(operation_models.RequirementQualificationMap)
                ),
                "audit": session.scalar(
                    select(func.count()).select_from(decision_models.AuditEvent)
                ),
            }
            audit = session.scalar(select(decision_models.AuditEvent))
    finally:
        engine.dispose()

    assert created.status_code == 201
    assert patched.status_code == 200
    assert patched.json()["status"] == "approved"
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["budget_cents"] == 2_500_000
    assert detail.status_code == 200
    assert detail.json()["mobilization_deadline"] == "2026-09-20T18:00:00Z"
    assert detail.json()["demands"][0]["quantity"] == 4
    assert detail.json()["requirements"][0]["code"] == "REQ-NR10"
    assert demand_patch.status_code == 200
    assert requirement_patch.status_code == 200
    assert updated_detail.json()["demands"][0]["quantity"] == 5
    assert updated_detail.json()["requirements"][0]["payload"]["minimum_experience_years"] == 3
    assert requirements.status_code == 200
    assert requirements.json()[0]["code"] == "REQ-NR10"
    assert counts == {
        "operations": 1,
        "demands": 1,
        "compatible": 1,
        "requirements": 1,
        "maps": 1,
        "audit": 4,
    }
    assert audit is not None
    assert audit.actor_id == "planner.ops@example.com"
