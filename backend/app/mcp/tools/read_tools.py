from typing import cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.dashboard.service import DashboardService
from app.decisions.repository import DecisionRepository
from app.fragility.service import FragilityService
from app.mcp.tools.registry import ToolRegistry
from app.mcp.tools.types import ToolContext, ToolDefinition
from app.operations.repository import OperationRepository
from app.workforce.profile_service import EmployeeProfileService
from app.workforce.repository import SQLAlchemyEmployeeRepository


class HorizonInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    horizon_days: int = Field(default=180, ge=1, le=730)


class OperationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


class EmployeeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: UUID


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_run_id: UUID


def _session(context: ToolContext) -> Session:
    if context.session is None:
        raise ValueError("tool_session_required")
    return context.session


def _dashboard(command: BaseModel, context: ToolContext) -> dict[str, object]:
    payload = cast(HorizonInput, command)
    return (
        DashboardService(_session(context))
        .get_overview(payload.horizon_days)
        .model_dump(mode="json")
    )


def _operation(command: BaseModel, context: ToolContext) -> dict[str, object]:
    payload = cast(OperationInput, command)
    result = OperationRepository(_session(context)).get_detail(payload.operation_id)
    if result is None:
        raise ValueError("operation_not_found")
    return result.model_dump(mode="json")


def _employee(command: BaseModel, context: ToolContext) -> dict[str, object]:
    payload = cast(EmployeeInput, command)
    result = EmployeeProfileService(SQLAlchemyEmployeeRepository(_session(context))).get_profile(
        payload.employee_id
    )
    data = result.model_dump(mode="json")
    data.pop("custos_incrementais", None)
    return data


def _fragility(command: BaseModel, context: ToolContext) -> dict[str, object]:
    payload = cast(HorizonInput, command)
    return (
        FragilityService(_session(context)).calculate(payload.horizon_days).model_dump(mode="json")
    )


def _decision(command: BaseModel, context: ToolContext) -> dict[str, object]:
    payload = cast(DecisionInput, command)
    result = DecisionRepository(_session(context)).get(payload.decision_run_id)
    if result is None:
        raise ValueError("decision_run_not_found")
    return result.model_dump(mode="json")


def build_read_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDefinition(
                "get_readiness_overview",
                "Indicadores executivos de prontidão.",
                HorizonInput,
                "read",
                _dashboard,
            ),
            ToolDefinition(
                "get_operation",
                "Operação, demandas e requisitos por ID.",
                OperationInput,
                "read",
                _operation,
            ),
            ToolDefinition(
                "get_employee_profile",
                "Perfil profissional sem custos individuais.",
                EmployeeInput,
                "read",
                _employee,
            ),
            ToolDefinition(
                "get_operational_fragility",
                "Cobertura e fragilidade explicável.",
                HorizonInput,
                "read",
                _fragility,
            ),
            ToolDefinition(
                "get_decision_run",
                "Cenário calculado e evidências por ID.",
                DecisionInput,
                "read",
                _decision,
            ),
        ]
    )
