from datetime import UTC, datetime
from uuid import uuid4

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


def test_outcome_api_compares_actuals_and_preserves_original_assignment() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    predicted_ready_at = datetime(2030, 3, 20, 8, tzinfo=UTC)
    actual_ready_at = datetime(2030, 3, 20, 9, 30, tzinfo=UTC)
    with Session(engine) as session:
        family = workforce_models.RoleFamily(code="OUT-FAM", name="Resultado")
        session.add(family)
        session.flush()
        role = workforce_models.Role(
            family_id=family.id,
            code="OUT-ROLE",
            name="Montador de resultado",
            active=True,
        )
        qualification = workforce_models.Qualification(
            code="OUT-QLF",
            name="Qualificação de resultado",
            category="segurança",
            active=True,
        )
        session.add_all((role, qualification))
        session.flush()
        original_employee = workforce_models.Employee(
            employee_number="OUT-001",
            name="Pessoa planejada",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        replacement_employee = workforce_models.Employee(
            employee_number="OUT-002",
            name="Pessoa substituta",
            canonical_role_id=role.id,
            base_location="Curitiba",
            seniority_level="pleno",
            active=True,
        )
        operation = operation_models.Operation(
            code="OUT-OPS",
            name="Operação realizada",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2030, 4, 1, tzinfo=UTC),
            ends_at=datetime(2030, 4, 30, tzinfo=UTC),
            mobilization_deadline=datetime(2030, 3, 20, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add_all((original_employee, replacement_employee, operation))
        session.flush()
        demand = operation_models.OperationRoleDemand(
            operation_id=operation.id,
            role_id=role.id,
            quantity=1,
            shift_code="day",
            priority=10,
        )
        catalog = workforce_models.TrainingCatalog(
            code="OUT-TRN",
            name="Curso planejado",
            qualification_id=qualification.id,
            duration_minutes=480,
            cost_cents=30_000,
            active=True,
        )
        session.add_all((demand, catalog))
        session.flush()
        run = decision_models.DecisionRun(
            operation_id=operation.id,
            objective="MIN_COST",
            solver_version="9.15",
            rules_version="1.0.0",
            input_snapshot_hash="4" * 64,
            status="OPTIMAL",
            runtime_ms=10,
            metrics={
                "total_incremental_cost_cents": 100_000,
                "team_ready_at_epoch_minutes": int(predicted_ready_at.timestamp() // 60),
            },
            candidate_snapshot=[],
            created_by="optimizer@example.com",
        )
        session.add(run)
        session.flush()
        assignment = decision_models.DecisionAssignment(
            decision_run_id=run.id,
            employee_id=original_employee.id,
            role_demand_id=demand.id,
            starts_at=operation.starts_at,
            ends_at=operation.ends_at,
            incremental_cost_cents=100_000,
        )
        training = decision_models.DecisionTrainingAction(
            decision_run_id=run.id,
            employee_id=original_employee.id,
            training_catalog_id=catalog.id,
            ready_at=predicted_ready_at,
            cost_cents=30_000,
            duration_minutes=480,
        )
        selection = decision_models.DecisionSelection(
            decision_run_id=run.id,
            operation_id=operation.id,
            actor_id="planner@example.com",
            note="Cenário aprovado",
            selected_at=datetime(2030, 1, 2, tzinfo=UTC),
        )
        session.add_all((assignment, training, selection))
        session.commit()
        run_id = run.id
        assignment_id = assignment.id
        training_id = training.id
        original_employee_id = original_employee.id
        replacement_employee_id = replacement_employee.id

    client = TestClient(create_app(session_factory=factory))
    try:
        invalid_reference = client.post(
            f"/decision-runs/{run_id}/outcome",
            headers={"X-TWR-Actor": "supervisor@example.com", "X-TWR-Role": "planner"},
            json={
                "actual_cost_cents": 125_000,
                "actual_ready_at": actual_ready_at.isoformat(),
                "substitutions": [
                    {
                        "original_assignment_id": str(assignment_id),
                        "actual_employee_id": str(uuid4()),
                    }
                ],
                "performed_training_action_ids": [str(training_id)],
            },
        )
        with Session(engine) as validation_session:
            outcomes_after_rejection = validation_session.scalars(
                select(decision_models.DecisionOutcome)
            ).all()
            outcome_events_after_rejection = validation_session.scalars(
                select(decision_models.AuditEvent).where(
                    decision_models.AuditEvent.event_type
                    == "decision.outcome_recorded"
                )
            ).all()
        response = client.post(
            f"/decision-runs/{run_id}/outcome",
            headers={"X-TWR-Actor": "supervisor@example.com", "X-TWR-Role": "planner"},
            json={
                "actual_cost_cents": 125_000,
                "actual_ready_at": actual_ready_at.isoformat(),
                "substitutions": [
                    {
                        "original_assignment_id": str(assignment_id),
                        "actual_employee_id": str(replacement_employee_id),
                    }
                ],
                "performed_training_action_ids": [str(training_id)],
                "calibration_observations": [
                    {
                        "parameter": "training_cost_cents",
                        "category": "seguranca",
                        "value": "32000",
                    }
                ],
            },
        )
        detail_response = client.get(f"/decision-runs/{run_id}")
    finally:
        client.close()

    assert response.status_code == 201
    assert invalid_reference.status_code == 422
    assert invalid_reference.json()["detail"]["code"] == "invalid_outcome_reference"
    assert outcomes_after_rejection == []
    assert outcome_events_after_rejection == []
    payload = response.json()
    assert payload["recorded_by"] == "supervisor@example.com"
    assert payload["comparison"]["cost"]["variance_cents"] == 25_000
    assert payload["comparison"]["readiness"]["variance_minutes"] == 90
    assert payload["comparison"]["assignments"]["substitution_count"] == 1
    assert payload["comparison"]["training"]["completion_percent"] == 100.0
    assert payload["calibration_observations"] == [
        {
            "parameter": "training_cost_cents",
            "category": "seguranca",
            "value": "32000",
        }
    ]
    substitution = payload["substitutions"][0]
    assert substitution["original_employee_id"] == str(original_employee_id)
    assert substitution["actual_employee_id"] == str(replacement_employee_id)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["outcome"]["id"] == payload["id"]
    assert detail["outcome_context"]["assignments"][0]["id"] == str(assignment_id)
    assert detail["outcome_context"]["training_actions"][0]["id"] == str(training_id)
    assert detail["timeline"][-1]["event_type"] == "decision.outcome_recorded"

    with Session(engine) as session:
        persisted_assignment = session.get(
            decision_models.DecisionAssignment, assignment_id
        )
        outcome = session.scalar(select(decision_models.DecisionOutcome))
        audit = session.scalar(
            select(decision_models.AuditEvent).where(
                decision_models.AuditEvent.event_type == "decision.outcome_recorded"
            )
        )
    assert persisted_assignment is not None
    assert persisted_assignment.employee_id == original_employee_id
    assert outcome is not None
    assert outcome.outcome_metrics["calibration_observations"] == [
        {
            "parameter": "training_cost_cents",
            "category": "seguranca",
            "value": "32000",
        }
    ]
    assert audit is not None
    engine.dispose()
