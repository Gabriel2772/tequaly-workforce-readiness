from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.decisions import models as decision_models  # noqa: F401
from app.main import create_app


def test_dashboard_api_returns_an_empty_but_actionable_overview() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    client = TestClient(create_app(session_factory=factory))
    try:
        response = client.get(
            "/dashboard/overview",
            params={"horizon_days": 90},
            headers={"X-TWR-Now": datetime(2030, 1, 1, tzinfo=UTC).isoformat()},
        )
    finally:
        client.close()

    assert response.status_code == 200
    payload = response.json()
    assert payload["horizon_days"] == 90
    assert payload["active_employee_count"] == 0
    assert payload["readiness_percent"] is None
    assert payload["upcoming_operations"] == []
    assert payload["risk_alerts"] == []
    engine.dispose()
