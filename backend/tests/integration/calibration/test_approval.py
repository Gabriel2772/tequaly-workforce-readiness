from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models
from app.main import create_app
from app.operations import models as operation_models


def test_calibration_suggestion_requires_explicit_confirmation_and_versions_parameter() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    samples = [100, 100, 110, 120, 10_000]
    with Session(engine) as session:
        operation = operation_models.Operation(
            code="CAL-OPS",
            name="Opera��o de calibra��o",
            client_name="Cliente",
            base_location="Curitiba",
            starts_at=datetime(2030, 4, 1, tzinfo=UTC),
            ends_at=datetime(2030, 4, 30, tzinfo=UTC),
            mobilization_deadline=datetime(2030, 3, 20, tzinfo=UTC),
            status="confirmed",
            budget_cents=None,
        )
        session.add(operation)
        session.flush()
        for index, value in enumerate(samples):
            run = decision_models.DecisionRun(
                operation_id=operation.id,
                objective="MIN_COST",
                solver_version="9.15",
                rules_version="1.0.0",
                input_snapshot_hash=f"{index + 5}" * 64,
                status="OPTIMAL",
                runtime_ms=10,
                metrics={},
                candidate_snapshot=[],
                created_by="optimizer@example.com",
            )
            session.add(run)
            session.flush()
            session.add(
                decision_models.DecisionOutcome(
                    decision_run_id=run.id,
                    selected=True,
                    outcome_metrics={
                        "calibration_observations": [
                            {
                                "parameter": "training_cost_cents",
                                "category": "seguranca",
                                "value": str(value),
                            }
                        ]
                    },
                    recorded_by="supervisor@example.com",
                )
            )
        session.add(
            decision_models.CalibrationParameter(
                name="training_cost_cents:seguranca",
                version="v1",
                value=Decimal("90"),
                rationale="Valor inicial",
            )
        )
        session.commit()

    headers = {"X-TWR-Actor": "admin@example.com", "X-TWR-Role": "admin"}
    client = TestClient(create_app(session_factory=factory))
    try:
        suggestion_response = client.post(
            "/calibration/suggestions",
            headers=headers,
            json={"parameter": "training_cost_cents", "category": "seguranca"},
        )
        suggestion_id = suggestion_response.json().get("id")
        rejected_apply = client.post(
            f"/calibration/suggestions/{suggestion_id}/apply",
            headers=headers,
            json={"confirmed": False},
        )
        with Session(engine) as rejection_session:
            count_after_rejection = rejection_session.scalar(
                select(func.count()).select_from(
                    decision_models.CalibrationParameter
                )
            )
        applied_response = client.post(
            f"/calibration/suggestions/{suggestion_id}/apply",
            headers=headers,
            json={"confirmed": True},
        )
    finally:
        client.close()

    assert suggestion_response.status_code == 201
    suggestion = suggestion_response.json()
    assert Decimal(suggestion["current_value"]) == Decimal("90")
    assert Decimal(suggestion["proposed_value"]) == Decimal("110")
    assert suggestion["sample_size"] == 5
    assert suggestion["confidence_basis"] == "median_iqr"
    assert rejected_apply.status_code == 409
    assert rejected_apply.json()["detail"]["code"] == "confirmation_required"
    assert count_after_rejection == 1
    assert applied_response.status_code == 200
    applied = applied_response.json()
    assert applied["name"] == "training_cost_cents:seguranca"
    assert applied["version"] == "v2"
    assert Decimal(applied["value"]) == Decimal("110")

    with Session(engine) as session:
        parameter_count = session.scalar(
            select(func.count()).select_from(decision_models.CalibrationParameter)
        )
        audit = session.scalar(
            select(decision_models.AuditEvent).where(
                decision_models.AuditEvent.event_type
                == "calibration.suggestion_applied"
            )
        )
    assert parameter_count == 2
    assert audit is not None
    engine.dispose()
