from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.operations.models import (
    EligibilityResult,
    EligibilityRun,
    Operation,
    OperationRoleDemand,
)
from app.training.investment_model import (
    InvestmentOpportunity,
    InvestmentProblem,
    solve_investment,
)
from app.training.types import (
    BenefitedOperation,
    InvestmentPlan,
    InvestmentPlanAction,
    InvestmentWeights,
)
from app.workforce.models import (
    Employee,
    EmployeeAssignment,
    EmployeeTrainingPlan,
    Qualification,
    TrainingCatalog,
    TrainingSession,
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _status_weight(status: str, weights: InvestmentWeights) -> int:
    normalized = status.strip().lower()
    if normalized == "confirmed":
        return weights.confirmed
    if normalized in {"probable", "planning"}:
        return weights.probable
    return weights.hypothetical


def _periods_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return _as_utc(first_start) < _as_utc(second_end) and _as_utc(second_start) < _as_utc(
        first_end
    )


class InvestmentPlanningService:
    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(UTC))

    def plan_investment(
        self,
        horizon: datetime,
        budget_cents: int,
        weights: InvestmentWeights,
    ) -> InvestmentPlan:
        now = _as_utc(self._clock())
        horizon = _as_utc(horizon)
        operations = tuple(
            self._session.scalars(
                select(Operation)
                .where(
                    func.coalesce(Operation.mobilization_deadline, Operation.starts_at) >= now,
                    func.coalesce(Operation.mobilization_deadline, Operation.starts_at) <= horizon,
                )
                .order_by(Operation.starts_at, Operation.id)
            )
        )
        operation_by_id = {operation.id: operation for operation in operations}
        operation_ids = set(operation_by_id)
        latest_runs: dict[UUID, EligibilityRun] = {}
        if operation_ids:
            runs = self._session.scalars(
                select(EligibilityRun)
                .where(
                    EligibilityRun.operation_id.in_(operation_ids),
                    EligibilityRun.status == "completed",
                )
                .order_by(
                    EligibilityRun.operation_id,
                    EligibilityRun.finished_at.desc(),
                    EligibilityRun.id.desc(),
                )
            )
            for run in runs:
                latest_runs.setdefault(run.operation_id, run)

        run_operation_ids = {run.id: operation_id for operation_id, run in latest_runs.items()}
        benefits_by_pair: dict[
            tuple[UUID, UUID], set[tuple[UUID, UUID]]
        ] = defaultdict(set)
        if run_operation_ids:
            results = self._session.scalars(
                select(EligibilityResult).where(
                    EligibilityResult.eligibility_run_id.in_(run_operation_ids),
                    EligibilityResult.classification == "TRAINABLE",
                )
            )
            for eligibility_result in results:
                qualification_ids: set[UUID] = set()
                for gap in eligibility_result.gaps:
                    raw_id = gap.get("qualification_id")
                    if raw_id is None:
                        continue
                    try:
                        qualification_ids.add(UUID(str(raw_id)))
                    except ValueError:
                        continue
                if len(qualification_ids) != 1:
                    continue
                qualification_id = next(iter(qualification_ids))
                operation_id = run_operation_ids[eligibility_result.eligibility_run_id]
                benefits_by_pair[(eligibility_result.employee_id, qualification_id)].add(
                    (operation_id, eligibility_result.role_demand_id)
                )

        employee_ids = {employee_id for employee_id, _ in benefits_by_pair}
        qualification_ids = {qualification_id for _, qualification_id in benefits_by_pair}
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
        demands = {
            demand.id: demand
            for demand in self._session.scalars(
                select(OperationRoleDemand).where(
                    OperationRoleDemand.operation_id.in_(operation_ids)
                )
            )
        }

        session_options: dict[
            UUID, list[tuple[TrainingSession, TrainingCatalog]]
        ] = defaultdict(list)
        if qualification_ids:
            rows = self._session.execute(
                select(TrainingSession, TrainingCatalog)
                .join(TrainingCatalog, TrainingCatalog.id == TrainingSession.training_catalog_id)
                .where(
                    TrainingCatalog.qualification_id.in_(qualification_ids),
                    TrainingCatalog.active.is_(True),
                    TrainingSession.status.in_(("scheduled", "open")),
                    TrainingSession.ends_at >= now,
                    TrainingSession.ends_at <= horizon,
                )
                .order_by(TrainingSession.ends_at, TrainingCatalog.cost_cents, TrainingSession.id)
            )
            for training_session, catalog in rows:
                session_options[catalog.qualification_id].append((training_session, catalog))

        enrolled_counts = {
            training_session_id: count
            for training_session_id, count in self._session.execute(
                select(EmployeeTrainingPlan.training_session_id, func.count())
                .where(EmployeeTrainingPlan.status.not_in(("cancelled", "canceled")))
                .group_by(EmployeeTrainingPlan.training_session_id)
            ).all()
        }
        unavailable_periods: dict[UUID, list[tuple[datetime, datetime]]] = defaultdict(list)
        if employee_ids:
            for assignment in self._session.scalars(
                select(EmployeeAssignment).where(
                    EmployeeAssignment.employee_id.in_(employee_ids),
                    EmployeeAssignment.status.not_in(
                        ("cancelled", "canceled", "completed")
                    ),
                )
            ):
                unavailable_periods[assignment.employee_id].append(
                    (assignment.starts_at, assignment.ends_at)
                )
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
                unavailable_periods[training_plan.employee_id].append(
                    (training_session.starts_at, training_session.ends_at)
                )
        opportunities: list[InvestmentOpportunity] = []
        metadata: dict[
            tuple[UUID, UUID, UUID],
            tuple[TrainingCatalog, list[tuple[Operation, UUID]]],
        ] = {}
        session_capacities: dict[UUID, int] = {}
        session_periods: dict[UUID, tuple[datetime, datetime]] = {}
        for (employee_id, qualification_id), raw_benefits in sorted(
            benefits_by_pair.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))
        ):
            for training_session, catalog in session_options.get(qualification_id, []):
                if any(
                    _periods_overlap(
                        training_session.starts_at,
                        training_session.ends_at,
                        unavailable_start,
                        unavailable_end,
                    )
                    for unavailable_start, unavailable_end in unavailable_periods[employee_id]
                ):
                    continue
                completes_at = _as_utc(training_session.ends_at)
                viable_benefits = [
                    (operation_by_id[operation_id], demand_id)
                    for operation_id, demand_id in raw_benefits
                    if completes_at
                    <= _as_utc(
                        operation_by_id[operation_id].mobilization_deadline
                        or operation_by_id[operation_id].starts_at
                    )
                ]
                if not viable_benefits:
                    continue
                benefited_operation_ids = tuple(
                    sorted({operation.id for operation, _ in viable_benefits}, key=str)
                )
                benefited_demand_ids = tuple(
                    sorted({demand_id for _, demand_id in viable_benefits}, key=str)
                )
                coverage_gain = sum(
                    _status_weight(operation.status, weights)
                    for operation, _ in viable_benefits
                )
                opportunity = InvestmentOpportunity(
                    employee_id=employee_id,
                    qualification_id=qualification_id,
                    training_catalog_id=catalog.id,
                    training_session_id=training_session.id,
                    completes_at=completes_at,
                    cost_cents=catalog.cost_cents,
                    coverage_gain=coverage_gain,
                    unlocked_position_count=len(benefited_demand_ids),
                    benefited_operation_ids=benefited_operation_ids,
                    benefited_demand_ids=benefited_demand_ids,
                )
                opportunities.append(opportunity)
                metadata[(employee_id, qualification_id, training_session.id)] = (
                    catalog,
                    viable_benefits,
                )
                session_capacities[training_session.id] = max(
                    0,
                    training_session.capacity - enrolled_counts.get(training_session.id, 0),
                )
                session_periods[training_session.id] = (
                    _as_utc(training_session.starts_at),
                    _as_utc(training_session.ends_at),
                )

        investment_result = solve_investment(
            InvestmentProblem(
                budget_cents=budget_cents,
                opportunities=tuple(opportunities),
                session_capacities=tuple(
                    sorted(session_capacities.items(), key=lambda item: str(item[0]))
                ),
                demand_capacities=tuple(
                    sorted(
                        ((demand.id, demand.quantity) for demand in demands.values()),
                        key=lambda item: str(item[0]),
                    )
                ),
                session_periods=tuple(
                    (session_id, starts_at, ends_at)
                    for session_id, (starts_at, ends_at) in sorted(
                        session_periods.items(), key=lambda item: str(item[0])
                    )
                ),
            )
        )
        actions: list[InvestmentPlanAction] = []
        for opportunity in investment_result.selected:
            catalog, selected_benefits = metadata[
                (
                    opportunity.employee_id,
                    opportunity.qualification_id,
                    opportunity.training_session_id,
                )
            ]
            benefits_by_operation: dict[UUID, list[UUID]] = defaultdict(list)
            for operation, demand_id in selected_benefits:
                benefits_by_operation[operation.id].append(demand_id)
            benefited_operations = [
                BenefitedOperation(
                    operation_id=operation_id,
                    operation_name=operation_by_id[operation_id].name,
                    weight=_status_weight(operation_by_id[operation_id].status, weights),
                    unlocked_position_count=len(set(demand_ids)),
                )
                for operation_id, demand_ids in sorted(
                    benefits_by_operation.items(), key=lambda item: str(item[0])
                )
            ]
            actions.append(
                InvestmentPlanAction(
                    employee_id=opportunity.employee_id,
                    employee_name=employees[opportunity.employee_id].name,
                    qualification_id=opportunity.qualification_id,
                    qualification_name=qualifications[opportunity.qualification_id].name,
                    training_catalog_id=opportunity.training_catalog_id,
                    training_name=catalog.name,
                    training_session_id=opportunity.training_session_id,
                    completes_at=opportunity.completes_at,
                    cost_cents=opportunity.cost_cents,
                    coverage_gain=opportunity.coverage_gain,
                    unlocked_position_count=opportunity.unlocked_position_count,
                    benefited_operations=benefited_operations,
                )
            )

        return InvestmentPlan(
            horizon=horizon,
            budget_cents=budget_cents,
            weights=weights,
            status=investment_result.status,
            actions=actions,
            total_cost_cents=investment_result.total_cost_cents,
            coverage_gain=investment_result.coverage_gain,
            unlocked_position_count=investment_result.unlocked_position_count,
            opportunity_count=len(opportunities),
            runtime_ms=investment_result.runtime_ms,
        )
