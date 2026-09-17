from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.fragility.rules import assess_risk, calculate_metric
from app.fragility.types import FragilityCell, FragilityReport
from app.operations.models import (
    EligibilityResult,
    EligibilityRun,
    Operation,
    OperationRequirement,
    OperationRoleDemand,
    RequirementQualificationMap,
)
from app.training.operation_service import (
    EligibilityRunRequiredForTrainingError,
    TrainingPlanningService,
)
from app.workforce.models import EmployeeAssignment, EmployeeQualification, Role


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class FragilityService:
    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(UTC))

    def calculate(
        self,
        horizon_days: int,
        operation_ids: Iterable[UUID] | None = None,
    ) -> FragilityReport:
        now = _as_utc(self._clock())
        horizon_at = now + timedelta(days=horizon_days)
        operation_query = select(Operation).where(
            func.coalesce(Operation.mobilization_deadline, Operation.starts_at) >= now,
            func.coalesce(Operation.mobilization_deadline, Operation.starts_at) <= horizon_at,
        )
        requested_ids = tuple(operation_ids or ())
        if requested_ids:
            operation_query = operation_query.where(Operation.id.in_(requested_ids))
        operations = tuple(
            self._session.scalars(
                operation_query.order_by(Operation.mobilization_deadline, Operation.id)
            )
        )
        operation_by_id = {operation.id: operation for operation in operations}
        scoped_operation_ids = set(operation_by_id)
        demands = tuple(
            self._session.scalars(
                select(OperationRoleDemand)
                .where(OperationRoleDemand.operation_id.in_(scoped_operation_ids))
                .order_by(OperationRoleDemand.operation_id, OperationRoleDemand.id)
            )
        )
        role_ids = {demand.role_id for demand in demands}
        roles = {
            role.id: role
            for role in self._session.scalars(select(Role).where(Role.id.in_(role_ids)))
        }

        latest_runs: dict[UUID, EligibilityRun] = {}
        if scoped_operation_ids:
            for run in self._session.scalars(
                select(EligibilityRun)
                .where(
                    EligibilityRun.operation_id.in_(scoped_operation_ids),
                    EligibilityRun.status == "completed",
                )
                .order_by(
                    EligibilityRun.operation_id,
                    EligibilityRun.finished_at.desc(),
                    EligibilityRun.id.desc(),
                )
            ):
                latest_runs.setdefault(run.operation_id, run)
        run_ids = {run.id for run in latest_runs.values()}
        eligible_by_demand: dict[UUID, set[UUID]] = defaultdict(set)
        trainable_by_demand: dict[UUID, set[UUID]] = defaultdict(set)
        if run_ids:
            for eligibility_result in self._session.scalars(
                select(EligibilityResult).where(
                    EligibilityResult.eligibility_run_id.in_(run_ids)
                )
            ):
                if eligibility_result.classification == "ELIGIBLE":
                    eligible_by_demand[eligibility_result.role_demand_id].add(
                        eligibility_result.employee_id
                    )
                elif eligibility_result.classification == "TRAINABLE":
                    trainable_by_demand[eligibility_result.role_demand_id].add(
                        eligibility_result.employee_id
                    )

        requirements = tuple(
            self._session.scalars(
                select(OperationRequirement).where(
                    OperationRequirement.operation_id.in_(scoped_operation_ids)
                )
            )
        )
        requirements_by_operation: dict[
            UUID, list[OperationRequirement]
        ] = defaultdict(list)
        for requirement in requirements:
            requirements_by_operation[requirement.operation_id].append(requirement)
        requirement_ids = {requirement.id for requirement in requirements}
        qualification_ids_by_requirement: dict[UUID, set[UUID]] = defaultdict(set)
        if requirement_ids:
            for requirement_id, qualification_id in self._session.execute(
                select(
                    RequirementQualificationMap.requirement_id,
                    RequirementQualificationMap.qualification_id,
                ).where(RequirementQualificationMap.requirement_id.in_(requirement_ids))
            ).all():
                qualification_ids_by_requirement[requirement_id].add(qualification_id)

        missing_sessions_by_demand: dict[UUID, int] = defaultdict(int)
        planning_service = TrainingPlanningService(self._session)
        for operation in operations:
            if operation.id not in latest_runs:
                continue
            try:
                training_plan = planning_service.for_operation(operation.id)
            except EligibilityRunRequiredForTrainingError:
                continue
            for blocker in training_plan.blockers:
                for demand_id in blocker.affected_demand_ids:
                    missing_sessions_by_demand[demand_id] += 1

        cells: list[FragilityCell] = []
        for demand in demands:
            operation = operation_by_id[demand.operation_id]
            deadline = _as_utc(operation.mobilization_deadline or operation.starts_at)
            eligible_employee_ids = eligible_by_demand[demand.id]
            applicable_requirements = [
                requirement
                for requirement in requirements_by_operation[operation.id]
                if requirement.role_demand_id in {None, demand.id}
            ]
            required_qualification_ids = {
                qualification_id
                for requirement in applicable_requirements
                for qualification_id in qualification_ids_by_requirement[requirement.id]
            }
            expiring_count = self._count_expiring(
                eligible_employee_ids,
                required_qualification_ids,
                now,
                deadline,
            )
            allocated_count = self._count_competing_allocations(
                eligible_employee_ids,
                operation,
            )
            metric = calculate_metric(
                required_count=demand.quantity,
                eligible_count=len(eligible_employee_ids),
                trainable_count=len(trainable_by_demand[demand.id]),
                expiring_count=expiring_count,
                allocated_count=allocated_count,
                missing_session_count=missing_sessions_by_demand[demand.id],
            )
            risk = assess_risk(metric)
            cells.append(
                FragilityCell(
                    operation_id=operation.id,
                    operation_name=operation.name,
                    operation_status=operation.status,
                    mobilization_deadline=deadline,
                    demand_id=demand.id,
                    role_id=demand.role_id,
                    role_name=roles[demand.role_id].name,
                    shift_code=demand.shift_code,
                    requirement_ids=[requirement.id for requirement in applicable_requirements],
                    requirement_names=[
                        requirement.name for requirement in applicable_requirements
                    ],
                    metric=metric,
                    risk=risk,
                )
            )

        summary = {severity: 0 for severity in ("low", "medium", "high", "critical")}
        for cell in cells:
            summary[cell.risk.severity] += 1
        return FragilityReport(
            generated_at=now,
            horizon_days=horizon_days,
            operation_count=len(operations),
            cells=cells,
            summary=summary,
        )

    def _count_expiring(
        self,
        employee_ids: set[UUID],
        qualification_ids: set[UUID],
        now: datetime,
        deadline: datetime,
    ) -> int:
        if not employee_ids or not qualification_ids:
            return 0
        return len(
            set(
                self._session.scalars(
                    select(EmployeeQualification.employee_id).where(
                        EmployeeQualification.employee_id.in_(employee_ids),
                        EmployeeQualification.qualification_id.in_(qualification_ids),
                        EmployeeQualification.expires_on.is_not(None),
                        EmployeeQualification.expires_on >= now.date(),
                        EmployeeQualification.expires_on <= deadline.date(),
                    )
                )
            )
        )

    def _count_competing_allocations(
        self,
        employee_ids: set[UUID],
        operation: Operation,
    ) -> int:
        if not employee_ids:
            return 0
        return len(
            set(
                self._session.scalars(
                    select(EmployeeAssignment.employee_id).where(
                        EmployeeAssignment.employee_id.in_(employee_ids),
                        EmployeeAssignment.operation_id != operation.id,
                        EmployeeAssignment.starts_at < operation.ends_at,
                        EmployeeAssignment.ends_at > operation.starts_at,
                        EmployeeAssignment.status.not_in(("cancelled", "canceled")),
                    )
                )
            )
        )
