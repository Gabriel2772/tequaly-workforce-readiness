from collections import defaultdict
from datetime import datetime
from uuid import UUID

from ortools.sat.python import cp_model

from app.eligibility.types import EligibilityStatus
from app.optimization.types import (
    Candidate,
    CandidateKey,
    Demand,
    InfeasibilityDiagnostic,
    OptimizationProblem,
    TrainingAction,
    TrainingKey,
)


def candidate_satisfies_hard_guards(candidate: Candidate, deadline: datetime) -> bool:
    if candidate.status is EligibilityStatus.INELIGIBLE:
        return False
    if candidate.status is EligibilityStatus.TRAINABLE and not candidate.required_training:
        return False
    return all(action.completes_at <= deadline for action in candidate.required_training)


def validate_problem(problem: OptimizationProblem) -> None:
    if problem.mobilization_deadline.utcoffset() is None:
        raise ValueError("mobilization deadline must be timezone-aware")
    demand_ids = [demand.demand_id for demand in problem.demands]
    if len(set(demand_ids)) != len(demand_ids):
        raise ValueError("duplicate demand")
    if any(demand.required_headcount <= 0 for demand in problem.demands):
        raise ValueError("required headcount must be positive")

    candidate_keys = [
        CandidateKey(candidate.employee_id, candidate.demand_id) for candidate in problem.candidates
    ]
    if len(set(candidate_keys)) != len(candidate_keys):
        raise ValueError("duplicate candidate")
    known_demand_ids = set(demand_ids)
    if any(candidate.demand_id not in known_demand_ids for candidate in problem.candidates):
        raise ValueError("candidate references unknown demand")
    if any(candidate.incremental_cost_cents < 0 for candidate in problem.candidates):
        raise ValueError("candidate cost must be nonnegative integer cents")
    for candidate in problem.candidates:
        if candidate.ready_at is not None and candidate.ready_at.utcoffset() is None:
            raise ValueError("candidate readiness must be timezone-aware")
        for action in candidate.required_training:
            if action.cost_cents < 0:
                raise ValueError("training cost must be nonnegative integer cents")
            if action.duration_minutes < 0:
                raise ValueError("training duration must be nonnegative integer minutes")
            if action.completes_at.utcoffset() is None:
                raise ValueError("training completion must be timezone-aware")

    known_candidate_keys = set(candidate_keys)
    if any(
        first not in known_candidate_keys or second not in known_candidate_keys
        for first, second in problem.conflicting_candidate_pairs
    ):
        raise ValueError("conflict references unknown candidate")


def precheck_problem(
    problem: OptimizationProblem,
) -> tuple[InfeasibilityDiagnostic, ...]:
    validate_problem(problem)
    demands_by_id = {demand.demand_id: demand for demand in problem.demands}
    allowed = tuple(
        candidate
        for candidate in problem.candidates
        if candidate.demand_id in demands_by_id
        and candidate_satisfies_hard_guards(candidate, problem.mobilization_deadline)
    )
    diagnostics: list[InfeasibilityDiagnostic] = []
    for demand in sorted(problem.demands, key=lambda item: str(item.demand_id)):
        available = len(
            {
                candidate.employee_id
                for candidate in allowed
                if candidate.demand_id == demand.demand_id
            }
        )
        if available < demand.required_headcount:
            diagnostics.append(
                InfeasibilityDiagnostic(
                    code=("no_candidates" if available == 0 else "insufficient_candidates"),
                    demand_id=demand.demand_id,
                    required_headcount=demand.required_headcount,
                    available_candidates=available,
                    uncovered_headcount=demand.required_headcount - available,
                    blocking_requirement_ids=demand.blocking_requirement_ids,
                    affected_demand_ids=(demand.demand_id,),
                )
            )
    if diagnostics:
        return tuple(diagnostics)

    slots = tuple(
        (demand.demand_id, index)
        for demand in sorted(problem.demands, key=lambda item: str(item.demand_id))
        for index in range(demand.required_headcount)
    )
    employee_demands: dict[UUID, set[UUID]] = defaultdict(set)
    for candidate in allowed:
        employee_demands[candidate.employee_id].add(candidate.demand_id)
    slots_by_employee = {
        employee_id: tuple(slot for slot in slots if slot[0] in demand_ids)
        for employee_id, demand_ids in employee_demands.items()
    }
    slot_to_employee: dict[tuple[UUID, int], UUID] = {}

    def assign(employee_id: UUID, seen: set[tuple[UUID, int]]) -> bool:
        for slot in slots_by_employee[employee_id]:
            if slot in seen:
                continue
            seen.add(slot)
            assigned_employee = slot_to_employee.get(slot)
            if assigned_employee is None or assign(assigned_employee, seen):
                slot_to_employee[slot] = employee_id
                return True
        return False

    for employee_id in sorted(slots_by_employee, key=str):
        assign(employee_id, set())

    matched = len(slot_to_employee)
    if matched < len(slots):
        requirement_ids = tuple(
            sorted(
                {
                    requirement_id
                    for demand in problem.demands
                    for requirement_id in demand.blocking_requirement_ids
                },
                key=str,
            )
        )
        return (
            InfeasibilityDiagnostic(
                code="workforce_capacity_shortfall",
                demand_id=None,
                required_headcount=len(slots),
                available_candidates=matched,
                uncovered_headcount=len(slots) - matched,
                blocking_requirement_ids=requirement_ids,
                affected_demand_ids=tuple(
                    sorted((demand.demand_id for demand in problem.demands), key=str)
                ),
            ),
        )
    return ()


def add_demand_coverage(
    model: cp_model.CpModel,
    demands: tuple[Demand, ...],
    assignment_variables: dict[CandidateKey, cp_model.IntVar],
) -> None:
    by_demand: dict[UUID, list[cp_model.IntVar]] = defaultdict(list)
    for key, variable in assignment_variables.items():
        by_demand[key.demand_id].append(variable)
    for demand in demands:
        model.add(sum(by_demand[demand.demand_id]) == demand.required_headcount)


def add_employee_uniqueness(
    model: cp_model.CpModel,
    assignment_variables: dict[CandidateKey, cp_model.IntVar],
) -> None:
    by_employee: dict[UUID, list[cp_model.IntVar]] = defaultdict(list)
    for key, variable in assignment_variables.items():
        by_employee[key.employee_id].append(variable)
    for variables in by_employee.values():
        model.add(sum(variables) <= 1)


def add_explicit_conflicts(
    model: cp_model.CpModel,
    conflicting_pairs: tuple[tuple[CandidateKey, CandidateKey], ...],
    assignment_variables: dict[CandidateKey, cp_model.IntVar],
) -> None:
    for first_key, second_key in conflicting_pairs:
        first = assignment_variables.get(first_key)
        second = assignment_variables.get(second_key)
        if first is not None and second is not None:
            model.add(first + second <= 1)


def add_required_training(
    model: cp_model.CpModel,
    candidates: dict[CandidateKey, Candidate],
    assignment_variables: dict[CandidateKey, cp_model.IntVar],
) -> tuple[
    dict[TrainingKey, cp_model.IntVar],
    dict[TrainingKey, TrainingAction],
]:
    training_variables: dict[TrainingKey, cp_model.IntVar] = {}
    training_actions: dict[TrainingKey, TrainingAction] = {}
    requiring_assignments: dict[TrainingKey, list[cp_model.IntVar]] = defaultdict(list)
    for candidate_key, candidate in candidates.items():
        assignment = assignment_variables[candidate_key]
        for action in candidate.required_training:
            training_key = TrainingKey(candidate.employee_id, action.training_catalog_id)
            training = training_variables.get(training_key)
            if training is None:
                training = model.new_bool_var(
                    f"train_{candidate.employee_id}_{action.training_catalog_id}"
                )
                training_variables[training_key] = training
                training_actions[training_key] = action
            model.add(assignment <= training)
            requiring_assignments[training_key].append(assignment)

    for training_key, training in training_variables.items():
        model.add(training <= sum(requiring_assignments[training_key]))
    return training_variables, training_actions
