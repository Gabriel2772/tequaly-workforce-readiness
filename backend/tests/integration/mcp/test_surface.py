from fastapi.testclient import TestClient

from app.main import create_app
from app.mcp.tools.read_tools import build_read_registry


def _client() -> TestClient:
    return TestClient(create_app())


def test_copilot_and_oauth_surfaces_are_absent() -> None:
    """Catch accidental registration of the removed Copilot or OAuth HTTP routes."""
    client = _client()

    assert client.get("/copilot/health").status_code == 404
    assert client.get("/.well-known/oauth-authorization-server").status_code == 404
    assert client.post("/oauth/token").status_code == 404


def test_local_mcp_keeps_five_read_only_tools() -> None:
    """Catch loss or write-capability expansion in the local MCP catalog."""
    catalog = build_read_registry().catalog()

    assert [item["name"] for item in catalog] == [
        "get_readiness_overview",
        "get_operation",
        "get_employee_profile",
        "get_operational_fragility",
        "get_decision_run",
    ]
    assert {item["effect"] for item in catalog} == {"read"}
