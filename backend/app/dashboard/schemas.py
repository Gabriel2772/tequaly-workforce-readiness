from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

RiskSeverity = Literal["low", "medium", "high", "critical"]
DashboardSeverity = Literal["unknown", "low", "medium", "high", "critical"]


class DashboardOperation(BaseModel):
    id: UUID
    name: str
    client_name: str
    status: str
    mobilization_deadline: datetime
    severity: DashboardSeverity
    analysis_status: Literal["pending", "completed"]
    readiness_percent: float | None
    uncovered_position_count: int


class DashboardRiskAlert(BaseModel):
    operation_id: UUID
    operation_name: str
    demand_id: UUID
    role_name: str
    shift_code: str
    severity: RiskSeverity
    required_count: int
    eligible_count: int
    uncovered_position_count: int
    explanation: str


class DashboardExpiry(BaseModel):
    employee_id: UUID
    employee_name: str
    qualification_id: UUID
    qualification_name: str
    expires_on: date
    days_remaining: int


class DashboardOverview(BaseModel):
    generated_at: datetime
    horizon_days: int
    active_employee_count: int
    readiness_percent: float | None
    expiring_qualification_count: int
    risky_operation_count: int
    uncovered_position_count: int
    planned_training_cost_cents: int
    upcoming_operations: list[DashboardOperation]
    risk_alerts: list[DashboardRiskAlert]
    expiring_qualifications: list[DashboardExpiry]
