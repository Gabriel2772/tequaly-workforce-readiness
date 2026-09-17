from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models
from app.main import create_app
from app.operations import models as operation_models
from app.workforce import models as workforce_models


def test_run_for_unknown_operation_returns_stable_not_found_error() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.post(
            "/operations/00000000-0000-0000-0000-000000000001/eligibility/run",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
        )
    finally:
        client.close()
        engine.dispose()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "operation_not_found"


def test_run_persists_results_and_never_evaluates_incompatible_roles() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    operation_start = datetime(2026, 10, 1, tzinfo=UTC)
    operation_end = datetime(2026, 10, 31, tzinfo=UTC)
    deadline = datetime(2026, 9, 20, tzinfo=UTC)

    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="FAM-ELG", name="Fam�lia Elegibilidade")
        session.add(family)
        session.flush()
        primary_role = workforce_models.Role(
            family_id=family.id, code="ROLE-ELG-1", name="Montador", active=True
        )
        compatible_role = workforce_models.Role(
            family_id=family.id, code="ROLE-ELG-2", name="Montador S�nior", active=True
        )
        incompatible_role = workforce_models.Role(
            family_id=family.id, code="ROLE-ELG-3", name="Analista", active=True
        )
        qualification = workforce_models.Qualification(
            code="QLF-ELG", name="NR-35", category="seguran�a", active=True
        )
        session.add_all((primary_role, compatible_role, incompatible_role, qualification))
        session.flush()

        operation = operation_models.Operation(
            code="OPS-ELG-001",
            name="Opera��o Elegibilidade",
            client_name="Cliente Teste",
            base_location="Curitiba",
            starts_at=operation_start,
            ends_at=operation_end,
            mobilization_deadline=deadline,
            status="planning",
            budget_cents=None,
        )
        session.add(operation)
        session.flush()
        demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=primary_role.id,
            quantity=2,
            shift_code="day",
            priority=10,
        )
        session.add(demand)
        session.flush()
        session.add(
            operation_models.OperationRoleCompatibleRole(
                role_demand_id=demand.id,
                role_id=compatible_role.id,
                preference_rank=1,
            )
        )
        requirement = operation_models.OperationRequirement(
            operation_id=operation.id,
            role_demand_id=demand.id,
            code="REQ-ELG-001",
            name="NR-35 v�lida",
            requirement_type="qualification",
            mandatory=True,
            payload={},
        )
        session.add(requirement)
        session.flush()
        session.add(
            operation_models.RequirementQualificationMap(
                requirement_id=requirement.id,
                qualification_id=qualification.id,
                minimum_level=None,
                allows_training=True,
            )
        )

        eligible = workforce_models.Employee(
            employee_number="ELG-001",
            name="Pessoa Eleg�vel",
            canonical_role_id=primary_role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            hired_on=date(2020, 1, 1),
            active=True,
        )
        trainable = workforce_models.Employee(
            employee_number="ELG-002",
            name="Pessoa Trein�vel",
            canonical_role_id=compatible_role.id,
            base_location="Curitiba",
            seniority_level="j�nior",
            hired_on=date(2024, 1, 1),
            active=True,
        )
        unavailable = workforce_models.Employee(
            employee_number="ELG-003",
            name="Pessoa Indispon�vel",
            canonical_role_id=primary_role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            hired_on=date(2021, 1, 1),
            active=True,
        )
        incompatible = workforce_models.Employee(
            employee_number="ELG-004",
            name="Pessoa Incompat�vel",
            canonical_role_id=incompatible_role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            hired_on=date(2020, 1, 1),
            active=True,
        )
        session.add_all((eligible, trainable, unavailable, incompatible))
        session.flush()
        session.add_all(
            (
                workforce_models.EmployeeAvailability(
                    employee_id=eligible.id,
                    starts_at=operation_start,
                    ends_at=operation_end,
                    status="available",
                ),
                workforce_models.EmployeeAvailability(
                    employee_id=trainable.id,
                    starts_at=operation_start,
                    ends_at=operation_end,
                    status="available",
                ),
                workforce_models.EmployeeQualification(
                    employee_id=eligible.id,
                    qualification_id=qualification.id,
                    issued_on=date(2025, 1, 1),
                    expires_on=date(2026, 10, 31),
                ),
                workforce_models.EmployeeQualification(
                    employee_id=unavailable.id,
                    qualification_id=qualification.id,
                    issued_on=date(2025, 1, 1),
                    expires_on=date(2026, 10, 31),
                ),
            )
        )
        training = workforce_models.TrainingCatalog(
            code="TRN-ELG",
            name="Forma��o NR-35",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=50_000,
            active=True,
        )
        session.add(training)
        session.flush()
        session.add(
            workforce_models.TrainingSession(
                training_catalog_id=training.id,
                starts_at=datetime(2026, 9, 18, tzinfo=UTC),
                ends_at=datetime(2026, 9, 19, tzinfo=UTC),
                capacity=20,
                base_location="Curitiba",
                status="scheduled",
            )
        )
        session.commit()
        operation_id = operation.id
        incompatible_id = incompatible.id

    client = TestClient(create_app(session_factory=factory))
    try:
        denied = client.post(
            f"/operations/{operation_id}/eligibility/run",
            headers={"X-TWR-Actor": "viewer@example.com", "X-TWR-Role": "viewer"},
        )
        response = client.post(
            f"/operations/{operation_id}/eligibility/run",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
        )
        repeated = client.post(
            f"/operations/{operation_id}/eligibility/run",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
        )
        latest = client.get(f"/operations/{operation_id}/eligibility/latest")
    finally:
        client.close()

    assert response.status_code == 201
    assert denied.status_code == 403
    payload = response.json()
    assert repeated.status_code == 201
    assert repeated.json()["input_hash"] == payload["input_hash"]
    assert latest.status_code == 200
    assert latest.json()["id"] == repeated.json()["id"]
    assert payload["rules_version"] == "1.0.0"
    assert payload["candidate_count"] == 3
    assert payload["evaluated_count"] == 3
    assert payload["eligible_count"] == 1
    assert payload["trainable_count"] == 1
    assert payload["ineligible_count"] == 1
    assert incompatible_id.hex not in {
        item["employee_id"].replace("-", "") for item in payload["results"]
    }
    trainable_result = next(
        item for item in payload["results"] if item["classification"] == "TRAINABLE"
    )
    unavailable_result = next(
        item for item in payload["results"] if item["classification"] == "INELIGIBLE"
    )
    assert trainable_result["required_training"]
    assert unavailable_result["reasons"][0]["code"] == "unavailable_for_operation"
    assert unavailable_result["reasons"][0]["details"]

    with Session(engine) as session:
        runs = session.scalars(select(operation_models.EligibilityRun)).all()
        results = session.scalars(select(operation_models.EligibilityResult)).all()
        audit = session.scalar(
            select(decision_models.AuditEvent).where(
                decision_models.AuditEvent.event_type == "eligibility.run_completed"
            )
        )

    assert len(runs) == 2
    assert len(results) == 6
    assert all(result.reason_codes is not None for result in results)
    assert audit is not None
    assert audit.payload["prefiltered_from"] == 4
    assert audit.payload["candidate_count"] == 3
