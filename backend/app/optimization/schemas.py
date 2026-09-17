from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.optimization.types import Objective, OptimizationStatus


class OptimizeCommand(BaseModel):
    objective: Objective


class OptimizationAssignmentView(BaseModel):
    employee_id: UUID
    demand_id: UUID
    starts_at: datetime
    ends_at: datetime
    incremental_cost_cents: int


class OptimizationTrainingView(BaseModel):
    employee_id: UUID
    training_catalog_id: UUID
    ready_at: datetime
    cost_cents: int
    duration_minutes: int


class OptimizationBlockerView(BaseModel):
    code: str
    demand_id: UUID | None
    required_headcount: int
    available_candidates: int
    uncovered_headcount: int
    blocking_requirement_ids: list[UUID]
    affected_demand_ids: list[UUID]


class OptimizationResultView(BaseModel):
    id: UUID
    operation_id: UUID
    objective: Objective
    status: OptimizationStatus
    solver_version: str
    rules_version: str
    input_snapshot_hash: str
    runtime_ms: int
    metrics: dict[str, object]
    assignments: list[OptimizationAssignmentView]
    training: list[OptimizationTrainingView]
    blockers: list[OptimizationBlockerView]
    created_by: str
    created_at: datetime


class ScenarioCollection(BaseModel):
    items: list[OptimizationResultView]
