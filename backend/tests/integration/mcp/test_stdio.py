import pytest
from mcp import Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dashboard.service import DashboardService
from app.db.base import Base
from app.demo.generator import generate_demo_dataset
from app.demo.seed import seed_demo
from app.mcp_server import build_mcp_server


@pytest.mark.asyncio
async def test_stdio_mcp_and_application_service_return_equivalent_overview() -> None:
    """Catch a moved tool core that no longer serves the local stdio MCP server."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        seed_demo(session, generate_demo_dataset(seed=42, employee_count=20))
        session.commit()
        expected = DashboardService(session).get_overview(30).model_dump(mode="json")

    try:
        async with Client(build_mcp_server(factory)) as client:
            tools = await client.list_tools()
            result = await client.call_tool("get_readiness_overview", {"horizon_days": 30})
    finally:
        engine.dispose()

    assert {tool.name for tool in tools.tools} == {
        "get_readiness_overview",
        "get_operation",
        "get_employee_profile",
        "get_operational_fragility",
        "get_decision_run",
    }
    actual = dict(result.structured_content or {})
    actual.pop("generated_at", None)
    expected.pop("generated_at", None)
    assert actual == expected
