from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import version
from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.decisions.service import DecisionPersistenceService
from app.eligibility.types import EligibilityStatus
from app.operations.models import (
    EligibilityResult as PersistedEligibilityResult,
)
from app.operations.models import (
    EligibilityRun,
    Operation,
    OperationRequirement,
    OperationRoleDemand,
)
from app.optimization.constraints import candidate_satisfies_hard_guards
from app.optimization.objectives import solve_problem
from app.optimization.schemas import OptimizationResultView
from app.optimization.types import (
    Candidate,
    CandidateKey,
    Demand,
    Objective,
    OptimizationProblem,
    TrainingAction,
    TrainingKey,
)
from app.workforce.models import (
    Employee,
    EmployeeAssignment,
    EmployeeCostProfile,
    TrainingCatalog,
)


class OperationOptimizationNotFoundError(LookupError):
    pass


class EligibilityRunRequiredError(RuntimeError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optimization_input_hash(
    eligibility_input_hash: str,
    problem: OptimizationProblem,
) -> str:
    payload = {
        "eligibility_input_hash": eligibility_input_hash,
        "operation_id": str(problem.operation_id),
        "mobilization_deadline": problem.mobilization_deadline.isoformat(),
        "demands": [
            {
                "demand_id": str(demand.demand_id),
                "required_headcount": demand.required_headcount,
                "blocking_requirement_ids": sorted(
                    str(value) for value in demand.blocking_requirement_ids
                ),
            }
            for demand in sorted(problem.demands, key=lambda value: str(value.demand_id))
        ],
        "candidates": [
            {
                "employee_id": str(candidate.employee_id),
                "demand_id": str(candidate.demand_id),
                "status": candidate.status.value,
                "incremental_cost_cents": candidate.incremental_cost_cents,
                "ready_at": candidate.ready_at.isoformat() if candidate.ready_at else None,
                "internal": candidate.internal,
                "utilization_score": candidate.utilization_score,
                "training": [
                    {
                        "training_catalog_id": str(action.training_catalog_id),
                        "completes_at": action.completes_at.isoformat(),
                        "cost_cents": action.cost_cents,
                        "duration_minutes": action.duration_minutes,
                    }
                    for action in sorted(
                        candidate.required_training,
                        key=lambda value: str(value.training_catalog_id),
                    )
                ],
            }
            for candidate in sorted(
                problem.candidates,
                key=lambda value: (str(value.demand_id), str(value.employee_id)),
            )
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class OptimizationService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def optimize(self, operation_id: UUID, objective: Objective) -> OptimizationResultView:
        operation = self._session.get(Operation, operation_id)
        if operation is None:
            raise OperationOptimizationNotFoundError(str(operation_id))
        eligibility_run = self._session.scalar(
            select(EligibilityRun)
            .where(
                EligibilityRun.operation_id == operation_id,
                EligibilityRun.status == "completed",
            )
            .order_by(EligibilityRun.finished_at.desc(), EligibilityRun.id.desc())
            .limit(1)
        )
        if eligibility_run is None:
            raise EligibilityRunRequiredError(str(operation_id))

        starts_at = _as_utc(operation.starts_at)
        ends_at = _as_utc(operation.ends_at)
        deadline = (
            _as_utc(operation.mobilization_deadline)
            if operation.mobilization_deadline is not None
            else starts_at
        )
        problem = self._build_problem(operation, eligibility_run, starts_at, ends_at, deadline)
        solution = solve_problem(problem, objective, time_limit_seconds=30.0)
        candidate_map = {
            CandidateKey(candidate.employee_id, candidate.demand_id): candidate
            for candidate in problem.candidates
            if candidate_satisfies_hard_guards(candidate, deadline)
        }
        training_actions = {
            TrainingKey(candidate.employee_id, action.training_catalog_id): action
            for candidate in candidate_map.values()
            for action in candidate.required_training
        }
        return DecisionPersistenceService(self._session, self._actor_id).persist(
            operation_id=operation_id,
            operation_starts_at=starts_at,
            operation_ends_at=ends_at,
            objective=objective,
            solution=solution,
            candidates=candidate_map,
            training_actions=training_actions,
            solver_version=version("ortools"),
            rules_version=eligibility_run.rules_version,
            input_snapshot_hash=_optimization_input_hash(eligibility_run.input_hash, problem),
            eligibility_run_id=eligibility_run.id,
        )

    def _build_problem(
        self,
        operation: Operation,
        eligibility_run: EligibilityRun,
        starts_at: datetime,
        ends_at: datetime,
        deadline: datetime,
    ) -> OptimizationProblem:
        demand_records = tuple(
            self._session.scalars(
                select(OperationRoleDemand)
                .where(OperationRoleDemand.operation_id == operation.id)
                .order_by(OperationRoleDemand.priority, OperationRoleDemand.id)
            )
        )
        requirement_records = tuple(
            self._session.scalars(
                select(OperationRequirement).where(
                    OperationRequirement.operation_id == operation.id,
                    OperationRequirement.mandatory.is_(True),
                )
            )
        )
        demands = tuple(
            Demand(
                demand_id=demand.id,
                required_headcount=demand.quantity,
                blocking_requirement_ids=tuple(
                    sorted(
                        (
                            requirement.id
                            for requirement in requirement_records
                            if requirement.role_demand_id in {None, demand.id}
                        ),
                        key=str,
                    )
                ),
            )
            for demand in demand_records
        )
        result_records = tuple(
            self._session.scalars(
                select(PersistedEligibilityResult)
                .where(
                    PersistedEligibilityResult.eligibility_run_id == eligibility_run.id,
                    PersistedEligibilityResult.classification.in_(("ELIGIBLE", "TRAINABLE")),
                )
                .order_by(
                    PersistedEligibilityResult.role_demand_id,
                    PersistedEligibilityResult.employee_id,
                )
            )
        )
        employee_ids = {result.employee_id for result in result_records}
        employees = {
            employee.id: employee
            for employee in self._session.scalars(
                select(Employee).where(Employee.id.in_(employee_ids))
            )
        }
        cost_profiles: dict[UUID, EmployeeCostProfile] = {}
        for profile in self._session.scalars(
            select(EmployeeCostProfile)
            .where(EmployeeCostProfile.employee_id.in_(employee_ids))
            .order_by(
                EmployeeCostProfile.employee_id,
                EmployeeCostProfile.effective_from.desc(),
            )
        ):
            if (
                profile.employee_id not in cost_profiles
                and profile.effective_from <= starts_at.date()
                and (profile.effective_to is None or profile.effective_to >= starts_at.date())
            ):
                cost_profiles[profile.employee_id] = profile

        assignment_counts = {
            employee_id: count
            for employee_id, count in self._session.execute(
                select(EmployeeAssignment.employee_id, func.count())
                .where(
                    EmployeeAssignment.employee_id.in_(employee_ids),
                    EmployeeAssignment.status.not_in(("cancelled", "canceled")),
                )
                .group_by(EmployeeAssignment.employee_id)
            ).all()
        }
        training_ids = {
            UUID(training_id)
            for result in result_records
            for training_id in result.required_training_ids
        }
        training_catalog = {
            training.id: training
            for training in self._session.scalars(
                select(TrainingCatalog).where(TrainingCatalog.id.in_(training_ids))
            )
        }
        operation_hours = ceil((ends_at - starts_at).total_seconds() / 3600)
        default_ready_at = _as_utc(eligibility_run.started_at)
        candidates: list[Candidate] = []
        for result in result_records:
            employee = employees[result.employee_id]
            selected_profile = cost_profiles.get(result.employee_id)
            assignment_cost = 0
            if selected_profile is not None:
                assignment_cost = selected_profile.hourly_cost_cents * operation_hours
                if employee.base_location != operation.base_location:
                    assignment_cost += selected_profile.travel_cost_cents
            ready_at = _as_utc(result.ready_at) if result.ready_at else default_ready_at
            actions = tuple(
                TrainingAction(
                    training_catalog_id=training_id,
                    completes_at=ready_at,
                    cost_cents=training_catalog[training_id].cost_cents,
                    duration_minutes=training_catalog[training_id].duration_minutes,
                )
                for training_id in sorted(
                    (UUID(training_id) for training_id in result.required_training_ids),
                    key=str,
                )
                if training_id in training_catalog
            )
            candidates.append(
                Candidate(
                    employee_id=result.employee_id,
                    demand_id=result.role_demand_id,
                    status=EligibilityStatus(result.classification),
                    required_training=actions,
                    incremental_cost_cents=assignment_cost,
                    ready_at=ready_at,
                    internal=True,
                    utilization_score=max(
                        0,
                        100 - int(assignment_counts.get(result.employee_id, 0)) * 10,
                    ),
                )
            )
        return OptimizationProblem(
            operation_id=operation.id,
            mobilization_deadline=deadline,
            demands=demands,
            candidates=tuple(candidates),
        )
