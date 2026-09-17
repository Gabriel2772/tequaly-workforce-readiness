from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_core_available() -> None:
    """Catch removal of the public health contract or an LLM status field."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_origin_can_preflight_authenticated_writes() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/decision-runs/00000000-0000-0000-0000-000000000000/select",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-twr-actor,x-twr-role",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "x-twr-actor" in response.headers["access-control-allow-headers"].lower()
