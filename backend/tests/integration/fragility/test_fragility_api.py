from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.main import create_app
from app.operations import models as operation_models
from app.workforce import models as workforce_models


def test_fragility_api_aggregates_role_risk_without_employee_details() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        family = workforce_models.RoleFamily(code="RISK-FAM", name="Risco")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="RISK-ROLE",
            name="Soldador de risco",
            active=True,
        )
        operation = operation_models.Operation(
            code="RISK-OPS",
            name="Parada crítica",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2030, 4, 1, tzinfo=UTC),
            ends_at=datetime(2030, 4, 30, tzinfo=UTC),
            mobilization_deadline=datetime(2030, 3, 20, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add_all((role, operation))
        session.flush()
        demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=2,
            shift_code="day",
            priority=10,
        )
        run = operation_models.EligibilityRun(
            operation_id=operation.id,
            rules_version="1.0.0",
            input_hash="f" * 64,
            status="completed",
            started_at=datetime(2030, 1, 1, tzinfo=UTC),
            finished_at=datetime(2030, 1, 1, 0, 0, 1, tzinfo=UTC),
            candidate_count=2,
            evaluated_count=2,
            eligible_count=2,
        )
        session.add_all((demand, run))
        session.flush()
        for index in range(2):
            employee = workforce_models.Employee(
                employee_number=f"RISK-{index}",
                name=f"Pessoa {index}",
                canonical_role_id=role.id,
                base_location="Curitiba",
                seniority_level="pleno",
                active=True,
            )
            session.add(employee)
            session.flush()
            session.add(
                operation_models.EligibilityResult(
                    eligibility_run_id=run.id,
                    employee_id=employee.id,
                    role_demand_id=demand.id,
                    classification="ELIGIBLE",
                    reason_codes=[],
                    reasons=[],
                    gaps=[],
                    required_training_ids=[],
                    incremental_cost_cents=0,
                )
            )

    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.get(
            "/risk/fragility",
            params={"horizon_days": 2_000, "operation_ids": str(operation.id)},
        )
    finally:
        client.close()

    assert response.status_code == 200
    payload = response.json()
    assert payload["operation_count"] == 1
    assert payload["summary"]["high"] == 1
    assert len(payload["cells"]) == 1
    cell = payload["cells"][0]
    assert cell["role_name"] == "Soldador de risco"
    assert cell["metric"]["coverage_ratio"] == 1.0
    assert cell["metric"]["redundancy"] == 0
    assert cell["metric"]["single_point_of_failure"] is True
    assert cell["risk"]["severity"] == "high"
    assert "employee_id" not in str(cell)
    engine.dispose()
