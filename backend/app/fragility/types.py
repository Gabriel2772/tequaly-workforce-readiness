from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

RiskSeverity = Literal["low", "medium", "high", "critical"]


class FragilityMetric(BaseModel):
    required_count: int
    eligible_count: int
    trainable_count: int
    expiring_count: int
    allocated_count: int
    missing_session_count: int
    coverage_ratio: float
    redundancy: int
    single_point_of_failure: bool


class RiskExplanation(BaseModel):
    code: str
    message: str
    threshold: int | float
    observed: int | float


class RiskAssessment(BaseModel):
    severity: RiskSeverity
    reason_codes: list[str]
    explanations: list[RiskExplanation]


class FragilityCell(BaseModel):
    operation_id: UUID
    operation_name: str
    operation_status: str
    mobilization_deadline: datetime
    demand_id: UUID
    role_id: UUID
    role_name: str
    shift_code: str
    requirement_ids: list[UUID]
    requirement_names: list[str]
    metric: FragilityMetric
    risk: RiskAssessment


class FragilityReport(BaseModel):
    generated_at: datetime
    horizon_days: int
    operation_count: int
    cells: list[FragilityCell]
    summary: dict[str, int]
