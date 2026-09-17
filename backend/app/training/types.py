from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OperationTrainingAction(BaseModel):
    employee_id: UUID
    employee_name: str
    qualification_id: UUID
    qualification_name: str
    training_catalog_id: UUID
    training_name: str
    training_session_id: UUID
    starts_at: datetime
    completes_at: datetime
    cost_cents: int
    duration_minutes: int
    affected_demand_ids: list[UUID]
    unlocked_position_count: int


class OperationTrainingBlocker(BaseModel):
    employee_id: UUID
    employee_name: str
    qualification_id: UUID
    qualification_name: str
    code: str
    message: str
    deadline: datetime
    affected_demand_ids: list[UUID]


class OperationTrainingPlan(BaseModel):
    operation_id: UUID
    decision_run_id: UUID | None
    mobilization_deadline: datetime
    actions: list[OperationTrainingAction]
    blockers: list[OperationTrainingBlocker]
    total_cost_cents: int
    total_duration_minutes: int
    unlocked_position_count: int


class InvestmentWeights(BaseModel):
    confirmed: int = Field(default=100, ge=0, le=10_000)
    probable: int = Field(default=60, ge=0, le=10_000)
    hypothetical: int = Field(default=30, ge=0, le=10_000)


class InvestmentPlanRequest(BaseModel):
    horizon: datetime
    budget_cents: int = Field(ge=0)
    weights: InvestmentWeights = Field(default_factory=InvestmentWeights)


class BenefitedOperation(BaseModel):
    operation_id: UUID
    operation_name: str
    weight: int
    unlocked_position_count: int


class InvestmentPlanAction(BaseModel):
    employee_id: UUID
    employee_name: str
    qualification_id: UUID
    qualification_name: str
    training_catalog_id: UUID
    training_name: str
    training_session_id: UUID
    completes_at: datetime
    cost_cents: int
    coverage_gain: int
    unlocked_position_count: int
    benefited_operations: list[BenefitedOperation]


class InvestmentPlan(BaseModel):
    horizon: datetime
    budget_cents: int
    weights: InvestmentWeights
    status: str
    actions: list[InvestmentPlanAction]
    total_cost_cents: int
    coverage_gain: int
    unlocked_position_count: int
    opportunity_count: int
    runtime_ms: int
