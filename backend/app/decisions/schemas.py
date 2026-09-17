from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.calibration.types import CalibrationObservation
from app.optimization.schemas import OptimizationResultView


class SelectScenarioCommand(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class SelectedDecision(BaseModel):
    id: UUID
    decision_run_id: UUID
    operation_id: UUID
    actor_id: str
    note: str | None
    selected_at: datetime
    supersedes_decision_run_id: UUID | None
    idempotent: bool = False


class DecisionTimelineEvent(BaseModel):
    event_type: str
    occurred_at: datetime
    actor_id: str | None
    payload: dict[str, object]


class DecisionRunTimeline(BaseModel):
    run: OptimizationResultView
    selection: SelectedDecision | None
    timeline: list[DecisionTimelineEvent]


class OutcomeCostComparison(BaseModel):
    predicted_cents: int
    actual_cents: int
    variance_cents: int
    variance_percent: float | None


class OutcomeReadinessComparison(BaseModel):
    predicted_at: datetime
    actual_at: datetime
    variance_minutes: int
    status: str


class OutcomeAssignmentComparison(BaseModel):
    substitution_count: int


class OutcomeTrainingComparison(BaseModel):
    planned_count: int
    performed_count: int
    unperformed_count: int
    completion_percent: float | None


class OutcomeComparison(BaseModel):
    cost: OutcomeCostComparison
    readiness: OutcomeReadinessComparison
    assignments: OutcomeAssignmentComparison
    training: OutcomeTrainingComparison


class OutcomeSubstitutionCommand(BaseModel):
    original_assignment_id: UUID
    actual_employee_id: UUID


class RecordOutcomeCommand(BaseModel):
    actual_cost_cents: int = Field(ge=0)
    actual_ready_at: datetime
    substitutions: list[OutcomeSubstitutionCommand] = Field(default_factory=list)
    performed_training_action_ids: list[UUID] = Field(default_factory=list)
    calibration_observations: list[CalibrationObservation] = Field(
        default_factory=list, max_length=50
    )

    @field_validator("actual_ready_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("actual_ready_at must include a timezone")
        return value


class OutcomeSubstitutionView(BaseModel):
    original_assignment_id: UUID
    role_demand_id: UUID
    original_employee_id: UUID
    actual_employee_id: UUID


class DecisionOutcomeView(BaseModel):
    id: UUID
    decision_run_id: UUID
    recorded_by: str
    recorded_at: datetime
    comparison: OutcomeComparison
    substitutions: list[OutcomeSubstitutionView]
    performed_training_action_ids: list[UUID]
    calibration_observations: list[CalibrationObservation]


class OutcomeAssignmentContext(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str
    role_demand_id: UUID


class OutcomeTrainingContext(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str
    training_catalog_id: UUID
    training_name: str


class DecisionOutcomeContext(BaseModel):
    assignments: list[OutcomeAssignmentContext]
    training_actions: list[OutcomeTrainingContext]


class DecisionRunDetail(BaseModel):
    run: OptimizationResultView
    selection: SelectedDecision | None
    timeline: list[DecisionTimelineEvent]
    outcome: DecisionOutcomeView | None
    outcome_context: DecisionOutcomeContext
