from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo, stable_demo_id
from app.main import create_app
from app.operations import models as operation_models  # noqa: F401
from app.workforce import models as workforce_models  # noqa: F401


def test_training_plan_api_requires_eligibility_and_returns_explainable_actions() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    dataset = generate_demo_dataset(seed=42, employee_count=300)
    operation_id = stable_demo_id(dataset.seed, "operation", dataset.operations[0].code)
    with factory.begin() as session:
        seed_demo(session, dataset)

    client = TestClient(create_app(session_factory=factory))
    headers = {"X-TWR-Actor": "planner@example.com", "X-TWR-Role": "planner"}
    try:
        before_eligibility = client.get(f"/operations/{operation_id}/training-plan")
        eligibility = client.post(
            f"/operations/{operation_id}/eligibility/run",
            headers=headers,
        )
        response = client.get(f"/operations/{operation_id}/training-plan")
    finally:
        client.close()

    assert before_eligibility.status_code == 409
    assert before_eligibility.json()["detail"]["code"] == "eligibility_run_required"
    assert eligibility.status_code == 201
    assert response.status_code == 200
    payload = response.json()
    assert payload["operation_id"] == str(operation_id)
    assert payload["decision_run_id"] is None
    assert payload["total_cost_cents"] >= 0
    assert payload["actions"] or payload["blockers"]
    if payload["actions"]:
        assert payload["actions"][0]["completes_at"] <= payload["mobilization_deadline"]
        assert payload["actions"][0]["employee_name"]

    engine.dispose()
