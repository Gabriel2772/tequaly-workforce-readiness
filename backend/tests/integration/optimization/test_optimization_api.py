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


def test_optimize_persists_scenario_and_lists_it_for_comparison() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    starts_at = datetime(2026, 10, 1, tzinfo=UTC)
    ends_at = datetime(2026, 10, 3, tzinfo=UTC)

    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="FAM-OPT", name="Fam�lia Otimiza��o")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="ROLE-OPT",
            name="Montador de Otimiza��o",
            active=True,
        )
        session.add(role)
        session.flush()
        operation = operation_models.Operation(
            code="OPS-OPT-001",
            name="Opera��o Otimiza��o",
            client_name="Cliente Otimiza��o",
            base_location="Curitiba",
            starts_at=starts_at,
            ends_at=ends_at,
            mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
            status="planning",
            budget_cents=None,
        )
        session.add(operation)
        session.flush()
        demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=1,
            shift_code="day",
            priority=10,
        )
        cheap = workforce_models.Employee(
            employee_number="OPT-001",
            name="Pessoa Econ�mica",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            hired_on=date(2020, 1, 1),
            active=True,
        )
        expensive = workforce_models.Employee(
            employee_number="OPT-002",
            name="Pessoa Cara",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            hired_on=date(2020, 1, 1),
            active=True,
        )
        session.add_all((demand, cheap, expensive))
        session.flush()
        session.add_all(
            (
                workforce_models.EmployeeAvailability(
                    employee_id=cheap.id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    status="available",
                ),
                workforce_models.EmployeeAvailability(
                    employee_id=expensive.id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    status="available",
                ),
                workforce_models.EmployeeCostProfile(
                    employee_id=cheap.id,
                    currency="BRL",
                    hourly_cost_cents=1_000,
                    travel_cost_cents=0,
                    effective_from=date(2026, 1, 1),
                ),
                workforce_models.EmployeeCostProfile(
                    employee_id=expensive.id,
                    currency="BRL",
                    hourly_cost_cents=2_000,
                    travel_cost_cents=0,
                    effective_from=date(2026, 1, 1),
                ),
            )
        )
        session.commit()
        operation_id = operation.id
        cheap_id = cheap.id

    client = TestClient(create_app(session_factory=factory))
    headers = {"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"}
    try:
        missing_eligibility = client.post(
            f"/operations/{operation_id}/optimize",
            headers=headers,
            json={"objective": "MIN_COST"},
        )
        eligibility = client.post(
            f"/operations/{operation_id}/eligibility/run",
            headers=headers,
        )
        optimized_responses = [
            client.post(
                f"/operations/{operation_id}/optimize",
                headers=headers,
                json={"objective": objective},
            )
            for objective in ("MIN_COST", "FASTEST_READY", "MAX_INTERNAL")
        ]
        scenarios = client.get(f"/operations/{operation_id}/scenarios")
    finally:
        client.close()

    assert missing_eligibility.status_code == 409
    assert missing_eligibility.json()["detail"]["code"] == "eligibility_run_required"
    assert eligibility.status_code == 201
    assert all(response.status_code == 201 for response in optimized_responses)
    payload = optimized_responses[0].json()
    assert payload["objective"] == "MIN_COST"
    assert payload["status"] == "OPTIMAL"
    assert payload["assignments"][0]["employee_id"] == str(cheap_id)
    assert payload["metrics"]["total_incremental_cost_cents"] > 0
    assert len(payload["input_snapshot_hash"]) == 64
    assert payload["input_snapshot_hash"] != eligibility.json()["input_hash"]
    assert scenarios.status_code == 200
    scenario_items = scenarios.json()["items"]
    assert {item["objective"] for item in scenario_items} == {
        "MIN_COST",
        "FASTEST_READY",
        "MAX_INTERNAL",
    }
    assert payload["id"] in {item["id"] for item in scenario_items}

    with Session(engine) as session:
        runs = session.scalars(select(decision_models.DecisionRun)).all()
        assignments = session.scalars(select(decision_models.DecisionAssignment)).all()
        audit = session.scalar(
            select(decision_models.AuditEvent).where(
                decision_models.AuditEvent.event_type == "decision.run_completed"
            )
        )

    assert len(runs) == 3
    assert len(assignments) == 3
    assert audit is not None
    engine.dispose()
