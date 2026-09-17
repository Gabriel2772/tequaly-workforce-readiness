from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.eligibility.types import EligibilityStatus


class EligibilityReasonView(BaseModel):
    code: str
    message: str
    details: dict[str, object]


class CandidateEligibilityView(BaseModel):
    employee_id: UUID
    demand_id: UUID
    classification: EligibilityStatus
    reasons: list[EligibilityReasonView]
    gaps: list[dict[str, object]]
    required_training: list[UUID]
    ready_at: datetime | None


class EligibilityRunView(BaseModel):
    id: UUID
    operation_id: UUID
    rules_version: str
    input_hash: str
    status: str
    started_at: datetime
    finished_at: datetime
    runtime_ms: int
    candidate_count: int
    evaluated_count: int
    eligible_count: int
    trainable_count: int
    ineligible_count: int
    results: list[CandidateEligibilityView]
