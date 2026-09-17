from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import create_session_factory
from app.mcp.tools.read_tools import build_read_registry
from app.mcp.tools.types import ToolContext

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def build_mcp_server(
    session_factory: sessionmaker[Session] | None = None,
) -> MCPServer[Any]:
    if session_factory is None:
        _engine, session_factory = create_session_factory()
    registry = build_read_registry()
    server: MCPServer[Any] = MCPServer(
        "tequaly-workforce-readiness",
        instructions=("Ferramentas somente de leitura. Não selecione cenários nem altere dados."),
    )

    def execute(name: str, arguments: dict[str, object]) -> dict[str, object]:
        assert session_factory is not None
        with session_factory() as session:
            return registry.execute(
                name,
                arguments,
                ToolContext(session=session, actor_id="mcp-local-viewer"),
            )

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def get_readiness_overview(horizon_days: int = 180) -> dict[str, object]:
        """Indicadores executivos de prontidão e cobertura."""
        return execute("get_readiness_overview", {"horizon_days": horizon_days})

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def get_operation(operation_id: str) -> dict[str, object]:
        """Detalhes, demandas e requisitos de uma operação."""
        return execute("get_operation", {"operation_id": operation_id})

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def get_employee_profile(employee_id: str) -> dict[str, object]:
        """Perfil profissional sem custos individuais."""
        return execute("get_employee_profile", {"employee_id": employee_id})

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def get_operational_fragility(horizon_days: int = 180) -> dict[str, object]:
        """Fragilidade e cobertura explicável por demanda."""
        return execute("get_operational_fragility", {"horizon_days": horizon_days})

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def get_decision_run(decision_run_id: str) -> dict[str, object]:
        """Cenário calculado e evidências auditáveis."""
        return execute("get_decision_run", {"decision_run_id": decision_run_id})

    return server


def main() -> None:
    build_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
