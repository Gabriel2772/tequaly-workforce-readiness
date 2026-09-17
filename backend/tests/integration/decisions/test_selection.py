from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models
from app.main import create_app
from app.operations import models as operation_models


def test_selection_requires_planner_and_records_idempotent_supersession_timeline() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with Session(engine) as session:
        operation = operation_models.Operation(
            code="SEL-OPS",
            name="Opera��o de sele��o",
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
        eligibility_run = operation_models.EligibilityRun(
            operation_id=operation.id,
            rules_version="1.0.0",
            input_hash="1" * 64,
            status="completed",
            started_at=datetime(2030, 1, 1, tzinfo=UTC),
            finished_at=datetime(2030, 1, 1, 0, 0, 1, tzinfo=UTC),
            candidate_count=0,
            evaluated_count=0,
        )
        session.add(eligibility_run)
        session.flush()
        first = decision_models.DecisionRun(
            operation_id=operation.id,
            objective="MIN_COST",
            solver_version="9.15",
            rules_version="1.0.0",
            input_snapshot_hash="2" * 64,
            status="OPTIMAL",
            runtime_ms=10,
            metrics={"eligibility_run_id": str(eligibility_run.id)},
            candidate_snapshot=[],
            created_by="optimizer@example.com",
        )
        second = decision_models.DecisionRun(
            operation_id=operation.id,
            objective="FASTEST_READY",
            solver_version="9.15",
            rules_version="1.0.0",
            input_snapshot_hash="3" * 64,
            status="OPTIMAL",
            runtime_ms=8,
            metrics={"eligibility_run_id": str(eligibility_run.id)},
            candidate_snapshot=[],
            created_by="optimizer@example.com",
        )
        session.add_all((first, second))
        session.commit()
        first_id, second_id = first.id, second.id

    client = TestClient(create_app(session_factory=factory))
    try:
        forbidden = client.post(
            f"/decision-runs/{first_id}/select",
            headers={"X-TWR-Actor": "viewer@example.com", "X-TWR-Role": "viewer"},
            json={"note": "Tentativa"},
        )
        selected = client.post(
            f"/decision-runs/{first_id}/select",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
            json={"note": "Menor custo validado"},
        )
        repeated = client.post(
            f"/decision-runs/{first_id}/select",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
            json={"note": "Menor custo validado"},
        )
        replacement = client.post(
            f"/decision-runs/{second_id}/select",
            headers={"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"},
            json={"note": "Prazo passou a ser priorit�rio"},
        )
        timeline = client.get(f"/decision-runs/{second_id}")
        collection = client.get("/decision-runs")
    finally:
        client.close()

    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "write_forbidden"
    assert selected.status_code == 200
    assert repeated.json()["id"] == selected.json()["id"]
    assert repeated.json()["idempotent"] is True
    assert replacement.status_code == 200
    assert replacement.json()["decision_run_id"] == str(second_id)
    assert replacement.json()["supersedes_decision_run_id"] == str(first_id)
    assert timeline.status_code == 200
    assert [event["event_type"] for event in timeline.json()["timeline"]][-2:] == [
        "decision.selection_superseded",
        "decision.scenario_selected",
    ]
    assert collection.status_code == 200
    assert len(collection.json()["items"]) == 2

    with Session(engine) as session:
        active = session.scalar(
            select(decision_models.DecisionSelection).where(
                decision_models.DecisionSelection.superseded_at.is_(None)
            )
        )
        selection_count = session.scalar(
            select(func.count()).select_from(decision_models.DecisionSelection)
        )
        event_count = session.scalar(
            select(func.count())
            .select_from(decision_models.AuditEvent)
            .where(
                decision_models.AuditEvent.event_type.in_(
                    ("decision.scenario_selected", "decision.selection_superseded")
                )
            )
        )
    assert active is not None
    assert active.decision_run_id == second_id
    assert active.actor_id == "planner@example.com"
    assert active.note == "Prazo passou a ser priorit�rio"
    assert selection_count == 2
    assert event_count == 3
    engine.dispose()
