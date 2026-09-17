from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calibration.types import CalibrationObservation
from app.decisions.models import (
    AuditEvent,
    DecisionAssignment,
    DecisionOutcome,
    DecisionRun,
    DecisionSelection,
    DecisionTrainingAction,
)
from app.decisions.schemas import (
    DecisionOutcomeContext,
    DecisionOutcomeView,
    OutcomeAssignmentComparison,
    OutcomeAssignmentContext,
    OutcomeComparison,
    OutcomeCostComparison,
    OutcomeReadinessComparison,
    OutcomeSubstitutionView,
    OutcomeTrainingComparison,
    OutcomeTrainingContext,
    RecordOutcomeCommand,
)
from app.workforce.models import Employee, TrainingCatalog


class OutcomeDecisionRunNotFoundError(LookupError):
    pass


class OutcomeSelectionRequiredError(RuntimeError):
    pass


class OutcomeAlreadyRecordedError(RuntimeError):
    pass


class OutcomeReferenceError(ValueError):
    pass


class OutcomeSnapshotError(RuntimeError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def calculate_outcome_comparison(
    *,
    predicted_cost_cents: int,
    actual_cost_cents: int,
    predicted_ready_at: datetime,
    actual_ready_at: datetime,
    planned_training_count: int,
    performed_training_count: int,
    substitution_count: int,
) -> OutcomeComparison:
    predicted_ready_at = _as_utc(predicted_ready_at)
    actual_ready_at = _as_utc(actual_ready_at)
    variance_cents = actual_cost_cents - predicted_cost_cents
    variance_minutes = round(
        (actual_ready_at - predicted_ready_at).total_seconds() / 60
    )
    readiness_status = (
        "delayed"
        if variance_minutes > 0
        else "advanced"
        if variance_minutes < 0
        else "on_time"
    )
    return OutcomeComparison(
        cost=OutcomeCostComparison(
            predicted_cents=predicted_cost_cents,
            actual_cents=actual_cost_cents,
            variance_cents=variance_cents,
            variance_percent=(
                round(variance_cents / predicted_cost_cents * 100, 2)
                if predicted_cost_cents
                else None
            ),
        ),
        readiness=OutcomeReadinessComparison(
            predicted_at=predicted_ready_at,
            actual_at=actual_ready_at,
            variance_minutes=variance_minutes,
            status=readiness_status,
        ),
        assignments=OutcomeAssignmentComparison(
            substitution_count=substitution_count
        ),
        training=OutcomeTrainingComparison(
            planned_count=planned_training_count,
            performed_count=performed_training_count,
            unperformed_count=max(planned_training_count - performed_training_count, 0),
            completion_percent=(
                round(performed_training_count / planned_training_count * 100, 2)
                if planned_training_count
                else None
            ),
        ),
    )


class DecisionOutcomeService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def record_outcome(
        self,
        decision_run_id: UUID,
        command: RecordOutcomeCommand,
    ) -> DecisionOutcomeView:
        run = self._session.get(DecisionRun, decision_run_id)
        if run is None:
            raise OutcomeDecisionRunNotFoundError(str(decision_run_id))
        selected = self._session.scalar(
            select(DecisionSelection).where(
                DecisionSelection.decision_run_id == decision_run_id,
                DecisionSelection.superseded_at.is_(None),
            )
        )
        if selected is None:
            raise OutcomeSelectionRequiredError(str(decision_run_id))
        if self._session.scalar(
            select(DecisionOutcome).where(
                DecisionOutcome.decision_run_id == decision_run_id
            )
        ) is not None:
            raise OutcomeAlreadyRecordedError(str(decision_run_id))

        raw_predicted_cost = run.metrics.get("total_incremental_cost_cents")
        raw_predicted_ready = run.metrics.get("team_ready_at_epoch_minutes")
        if not isinstance(raw_predicted_cost, int) or not isinstance(
            raw_predicted_ready, int
        ):
            raise OutcomeSnapshotError(str(decision_run_id))
        predicted_ready_at = datetime.fromtimestamp(raw_predicted_ready * 60, UTC)

        assignments = {
            assignment.id: assignment
            for assignment in self._session.scalars(
                select(DecisionAssignment).where(
                    DecisionAssignment.decision_run_id == decision_run_id
                )
            )
        }
        substitutions: list[OutcomeSubstitutionView] = []
        seen_assignments: set[UUID] = set()
        for substitution in command.substitutions:
            assignment = assignments.get(substitution.original_assignment_id)
            if assignment is None or substitution.original_assignment_id in seen_assignments:
                raise OutcomeReferenceError("invalid original assignment")
            if self._session.get(Employee, substitution.actual_employee_id) is None:
                raise OutcomeReferenceError("invalid replacement employee")
            seen_assignments.add(substitution.original_assignment_id)
            if assignment.employee_id == substitution.actual_employee_id:
                continue
            substitutions.append(
                OutcomeSubstitutionView(
                    original_assignment_id=assignment.id,
                    role_demand_id=assignment.role_demand_id,
                    original_employee_id=assignment.employee_id,
                    actual_employee_id=substitution.actual_employee_id,
                )
            )

        planned_training_ids = set(
            self._session.scalars(
                select(DecisionTrainingAction.id).where(
                    DecisionTrainingAction.decision_run_id == decision_run_id
                )
            )
        )
        performed_training_ids = set(command.performed_training_action_ids)
        if not performed_training_ids.issubset(planned_training_ids):
            raise OutcomeReferenceError("invalid performed training action")

        comparison = calculate_outcome_comparison(
            predicted_cost_cents=raw_predicted_cost,
            actual_cost_cents=command.actual_cost_cents,
            predicted_ready_at=predicted_ready_at,
            actual_ready_at=command.actual_ready_at,
            planned_training_count=len(planned_training_ids),
            performed_training_count=len(performed_training_ids),
            substitution_count=len(substitutions),
        )
        substitutions_payload = [
            item.model_dump(mode="json") for item in substitutions
        ]
        outcome_metrics: dict[str, object] = {
            "actual_cost_cents": command.actual_cost_cents,
            "actual_ready_at": _as_utc(command.actual_ready_at).isoformat(),
            "comparison": comparison.model_dump(mode="json"),
            "substitutions": substitutions_payload,
            "performed_training_action_ids": [
                str(training_id)
                for training_id in sorted(performed_training_ids, key=str)
            ],
            "calibration_observations": [
                observation.model_dump(mode="json")
                for observation in command.calibration_observations
            ],
        }
        outcome = DecisionOutcome(
            decision_run_id=decision_run_id,
            selected=True,
            outcome_metrics=outcome_metrics,
            recorded_by=self._actor_id,
        )
        self._session.add(outcome)
        self._session.flush()
        occurred_at = datetime.now(UTC)
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="decision.outcome_recorded",
                aggregate_type="decision_run",
                aggregate_id=decision_run_id,
                payload={
                    "outcome_id": str(outcome.id),
                    "cost_variance_cents": comparison.cost.variance_cents,
                    "readiness_variance_minutes": comparison.readiness.variance_minutes,
                    "substitution_count": comparison.assignments.substitution_count,
                    "performed_training_count": comparison.training.performed_count,
                },
                occurred_at=occurred_at,
            )
        )
        self._session.flush()
        return DecisionOutcomeView(
            id=outcome.id,
            decision_run_id=decision_run_id,
            recorded_by=outcome.recorded_by,
            recorded_at=outcome.created_at,
            comparison=comparison,
            substitutions=substitutions,
            performed_training_action_ids=sorted(performed_training_ids, key=str),
            calibration_observations=command.calibration_observations,
        )


def get_outcome_view(
    session: Session,
    decision_run_id: UUID,
) -> DecisionOutcomeView | None:
    outcome = session.scalar(
        select(DecisionOutcome).where(
            DecisionOutcome.decision_run_id == decision_run_id
        )
    )
    if outcome is None:
        return None
    raw = outcome.outcome_metrics
    raw_substitutions = raw.get("substitutions", [])
    substitutions = raw_substitutions if isinstance(raw_substitutions, list) else []
    raw_training_ids = raw.get("performed_training_action_ids", [])
    training_ids = raw_training_ids if isinstance(raw_training_ids, list) else []
    raw_calibration_observations = raw.get("calibration_observations", [])
    calibration_observations = (
        raw_calibration_observations
        if isinstance(raw_calibration_observations, list)
        else []
    )
    return DecisionOutcomeView(
        id=outcome.id,
        decision_run_id=decision_run_id,
        recorded_by=outcome.recorded_by,
        recorded_at=outcome.created_at,
        comparison=OutcomeComparison.model_validate(raw["comparison"]),
        substitutions=[
            OutcomeSubstitutionView.model_validate(item)
            for item in substitutions
            if isinstance(item, dict)
        ],
        performed_training_action_ids=[
            UUID(str(value))
            for value in training_ids
        ],
        calibration_observations=[
            CalibrationObservation.model_validate(item)
            for item in calibration_observations
            if isinstance(item, dict)
        ],
    )


def get_outcome_context(
    session: Session,
    decision_run_id: UUID,
) -> DecisionOutcomeContext:
    assignments = list(
        session.scalars(
            select(DecisionAssignment).where(
                DecisionAssignment.decision_run_id == decision_run_id
            )
        )
    )
    training_actions = list(
        session.scalars(
            select(DecisionTrainingAction).where(
                DecisionTrainingAction.decision_run_id == decision_run_id
            )
        )
    )
    employee_ids = {assignment.employee_id for assignment in assignments}
    employee_ids.update(action.employee_id for action in training_actions)
    employees = {
        employee.id: employee
        for employee in session.scalars(
            select(Employee).where(Employee.id.in_(employee_ids))
        )
    }
    catalog_ids = {action.training_catalog_id for action in training_actions}
    catalogs = {
        catalog.id: catalog
        for catalog in session.scalars(
            select(TrainingCatalog).where(TrainingCatalog.id.in_(catalog_ids))
        )
    }
    return DecisionOutcomeContext(
        assignments=[
            OutcomeAssignmentContext(
                id=assignment.id,
                employee_id=assignment.employee_id,
                employee_name=employees[assignment.employee_id].name,
                role_demand_id=assignment.role_demand_id,
            )
            for assignment in assignments
        ],
        training_actions=[
            OutcomeTrainingContext(
                id=action.id,
                employee_id=action.employee_id,
                employee_name=employees[action.employee_id].name,
                training_catalog_id=action.training_catalog_id,
                training_name=catalogs[action.training_catalog_id].name,
            )
            for action in training_actions
        ],
    )
