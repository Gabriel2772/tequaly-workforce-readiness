from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.main import create_app


def test_quality_overview_exposes_actionable_source_backed_issues() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()

    response = TestClient(create_app(session_factory=factory)).get("/data-quality/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_employees"] > 0
    assert 0 <= payload["complete_profiles"] <= payload["active_employees"]
    assert {issue["code"] for issue in payload["issues"]} == {
        "incomplete_employee_profile",
        "employee_without_qualification",
        "expired_qualification",
        "employee_without_cost",
        "operation_without_eligibility",
    }
    assert all(issue["action"] for issue in payload["issues"])
    assert payload["source_mode"] == "synthetic_demo"
