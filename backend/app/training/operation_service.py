from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.decisions.models import DecisionAssignment, DecisionRun, DecisionTrainingAction
from app.operations.models import EligibilityResult, EligibilityRun, Operation
from app.training.types import (
    OperationTrainingAction,
    OperationTrainingBlocker,
    OperationTrainingPlan,
)
from app.workforce.models import (
    Employee,
    EmployeeAssignment,
    EmployeeTrainingPlan,
    Qualification,
    TrainingCatalog,
    TrainingSession,
)


class TrainingOperationNotFoundError(LookupError):
    pass


class TrainingDecisionRunNotFoundError(LookupError):
    pass


class EligibilityRunRequiredForTrainingError(RuntimeError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _periods_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return _as_utc(first_start) < _as_utc(second_end) and _as_utc(
        first_end
    ) > _as_utc(second_start)


class TrainingPlanningService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def materialize_for_decision(self, decision_run_id: UUID) -> OperationTrainingPlan:
        decision = self._session.get(DecisionRun, decision_run_id)
        if decision is None:
            raise TrainingDecisionRunNotFoundError(str(decision_run_id))
        plan = self.for_operation(decision.operation_id, decision_run_id)
        existing = {
            (action.employee_id, action.training_catalog_id): action
            for action in self._session.scalars(
                select(DecisionTrainingAction).where(
                    DecisionTrainingAction.decision_run_id == decision_run_id
                )
            )
        }
        for action in plan.actions:
            key = (action.employee_id, action.training_catalog_id)
            record = existing.get(key)
            if record is None:
                record = DecisionTrainingAction(
                    decision_run_id=decision_run_id,
                    employee_id=action.employee_id,
                    training_catalog_id=action.training_catalog_id,
                )
                self._session.add(record)
            record.training_session_id = action.training_session_id
            record.ready_at = action.completes_at
            record.cost_cents = action.cost_cents
            record.duration_minutes = action.duration_minutes
        self._session.flush()
        return plan

    def for_operation(
        self,
        operation_id: UUID,
        decision_run_id: UUID | None = None,
    ) -> OperationTrainingPlan:
        operation = self._session.get(Operation, operation_id)
        if operation is None:
            raise TrainingOperationNotFoundError(str(operation_id))
        deadline = _as_utc(operation.mobilization_deadline or operation.starts_at)

        eligible_pairs: set[tuple[UUID, UUID]] | None = None
        decision_eligibility_run_id: UUID | None = None
        if decision_run_id is not None:
            decision = self._session.get(DecisionRun, decision_run_id)
            if decision is None or decision.operation_id != operation_id:
                raise TrainingDecisionRunNotFoundError(str(decision_run_id))
            eligible_pairs = {
                (employee_id, demand_id)
                for employee_id, demand_id in self._session.execute(
                    select(DecisionAssignment.employee_id, DecisionAssignment.role_demand_id).where(
                        DecisionAssignment.decision_run_id == decision_run_id
                    )
                ).all()
            }
            raw_eligibility_run_id = decision.metrics.get("eligibility_run_id")
            if raw_eligibility_run_id is not None:
                try:
                    decision_eligibility_run_id = UUID(str(raw_eligibility_run_id))
                except ValueError:
                    decision_eligibility_run_id = None

        run_query = select(EligibilityRun).where(
            EligibilityRun.operation_id == operation_id,
            EligibilityRun.status == "completed",
        )
        if decision_eligibility_run_id is not None:
            run_query = run_query.where(EligibilityRun.id == decision_eligibility_run_id)
        else:
            run_query = run_query.order_by(
                EligibilityRun.finished_at.desc(), EligibilityRun.id.desc()
            ).limit(1)
        run = self._session.scalar(run_query)
        if run is None:
            raise EligibilityRunRequiredForTrainingError(str(operation_id))

        results = tuple(
            self._session.scalars(
                select(EligibilityResult)
                .where(
                    EligibilityResult.eligibility_run_id == run.id,
                    EligibilityResult.classification == "TRAINABLE",
                )
                .order_by(EligibilityResult.employee_id, EligibilityResult.role_demand_id)
            )
        )
        gaps: dict[tuple[UUID, UUID], set[UUID]] = defaultdict(set)
        for result in results:
            result_key = (result.employee_id, result.role_demand_id)
            if eligible_pairs is not None and result_key not in eligible_pairs:
                continue
            for raw_gap in result.gaps:
                raw_qualification_id = raw_gap.get("qualification_id")
                if raw_qualification_id is None:
                    continue
                try:
                    qualification_id = UUID(str(raw_qualification_id))
                except ValueError:
                    continue
                gaps[(result.employee_id, qualification_id)].add(result.role_demand_id)

        employee_ids = {employee_id for employee_id, _ in gaps}
        qualification_ids = {qualification_id for _, qualification_id in gaps}
        employees = {
            employee.id: employee
            for employee in self._session.scalars(
                select(Employee).where(Employee.id.in_(employee_ids))
            )
        }
        qualifications = {
            qualification.id: qualification
            for qualification in self._session.scalars(
                select(Qualification).where(Qualification.id.in_(qualification_ids))
            )
        }
        session_options: dict[
            UUID, list[tuple[TrainingSession, TrainingCatalog]]
        ] = defaultdict(list)
        if qualification_ids:
            for training_session, catalog in self._session.execute(
                select(TrainingSession, TrainingCatalog)
                .join(TrainingCatalog, TrainingCatalog.id == TrainingSession.training_catalog_id)
                .where(
                    TrainingCatalog.qualification_id.in_(qualification_ids),
                    TrainingCatalog.active.is_(True),
                    TrainingSession.status.in_(("scheduled", "open")),
                )
                .order_by(
                    TrainingSession.ends_at,
                    TrainingCatalog.cost_cents,
                    TrainingSession.id,
                )
            ).all():
                if _as_utc(training_session.ends_at) <= deadline:
                    session_options[catalog.qualification_id].append((training_session, catalog))

        enrolled_counts = {
            training_session_id: count
            for training_session_id, count in self._session.execute(
                select(EmployeeTrainingPlan.training_session_id, func.count())
                .where(EmployeeTrainingPlan.status.not_in(("cancelled", "canceled")))
                .group_by(EmployeeTrainingPlan.training_session_id)
            ).all()
        }
        assignment_periods: dict[UUID, list[tuple[datetime, datetime]]] = defaultdict(list)
        if employee_ids:
            for assignment in self._session.scalars(
                select(EmployeeAssignment).where(
                    EmployeeAssignment.employee_id.in_(employee_ids),
                    EmployeeAssignment.status.not_in(("cancelled", "canceled", "completed")),
                )
            ):
                assignment_periods[assignment.employee_id].append(
                    (assignment.starts_at, assignment.ends_at)
                )
        existing_training_periods: dict[
            UUID, list[tuple[datetime, datetime]]
        ] = defaultdict(list)
        if employee_ids:
            for training_plan, training_session in self._session.execute(
                select(EmployeeTrainingPlan, TrainingSession)
                .join(
                    TrainingSession,
                    TrainingSession.id == EmployeeTrainingPlan.training_session_id,
                )
                .where(
                    EmployeeTrainingPlan.employee_id.in_(employee_ids),
                    EmployeeTrainingPlan.status.not_in(
                        ("cancelled", "canceled", "completed")
                    ),
                )
            ).all():
                existing_training_periods[training_plan.employee_id].append(
                    (training_session.starts_at, training_session.ends_at)
                )
        planned_counts: dict[UUID, int] = defaultdict(int)
        planned_periods: dict[UUID, list[tuple[datetime, datetime]]] = defaultdict(list)
        actions: list[OperationTrainingAction] = []
        blockers: list[OperationTrainingBlocker] = []
        for (employee_id, qualification_id), demand_ids in sorted(
            gaps.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))
        ):
            employee = employees[employee_id]
            qualification = qualifications[qualification_id]
            selected: tuple[TrainingSession, TrainingCatalog] | None = None
            for option in session_options.get(qualification_id, []):
                training_session, _ = option
                occupied = (
                    enrolled_counts.get(training_session.id, 0)
                    + planned_counts[training_session.id]
                )
                unavailable_periods = (
                    assignment_periods[employee_id]
                    + existing_training_periods[employee_id]
                    + planned_periods[employee_id]
                )
                conflicts = any(
                    _periods_overlap(
                        training_session.starts_at,
                        training_session.ends_at,
                        period_start,
                        period_end,
                    )
                    for period_start, period_end in unavailable_periods
                )
                if occupied < training_session.capacity and not conflicts:
                    selected = option
                    break
            affected_demand_ids = sorted(demand_ids, key=str)
            if selected is None:
                blockers.append(
                    OperationTrainingBlocker(
                        employee_id=employee_id,
                        employee_name=employee.name,
                        qualification_id=qualification_id,
                        qualification_name=qualification.name,
                        code="no_session_before_deadline",
                        message="Nenhuma turma com vaga termina antes da mobiliza��o.",
                        deadline=deadline,
                        affected_demand_ids=affected_demand_ids,
                    )
                )
                continue
            training_session, catalog = selected
            planned_counts[training_session.id] += 1
            planned_periods[employee_id].append(
                (training_session.starts_at, training_session.ends_at)
            )
            actions.append(
                OperationTrainingAction(
                    employee_id=employee_id,
                    employee_name=employee.name,
                    qualification_id=qualification_id,
                    qualification_name=qualification.name,
                    training_catalog_id=catalog.id,
                    training_name=catalog.name,
                    training_session_id=training_session.id,
                    starts_at=_as_utc(training_session.starts_at),
                    completes_at=_as_utc(training_session.ends_at),
                    cost_cents=catalog.cost_cents,
                    duration_minutes=catalog.duration_minutes,
                    affected_demand_ids=affected_demand_ids,
                    unlocked_position_count=len(affected_demand_ids),
                )
            )

        return OperationTrainingPlan(
            operation_id=operation_id,
            decision_run_id=decision_run_id,
            mobilization_deadline=deadline,
            actions=actions,
            blockers=blockers,
            total_cost_cents=sum(action.cost_cents for action in actions),
            total_duration_minutes=sum(action.duration_minutes for action in actions),
            unlocked_position_count=sum(action.unlocked_position_count for action in actions),
        )
