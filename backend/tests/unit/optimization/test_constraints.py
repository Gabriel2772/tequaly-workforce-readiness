import random
from datetime import UTC, datetime
from uuid import uuid4

from ortools.sat.python import cp_model

from app.eligibility.types import EligibilityStatus
from app.optimization.model_builder import build_assignment_model
from app.optimization.types import (
    Candidate,
    CandidateKey,
    Demand,
    OptimizationProblem,
    TrainingAction,
    TrainingKey,
)


def test_model_covers_each_demand_without_assigning_one_person_twice() -> None:
    operation_id = uuid4()
    first_demand_id = uuid4()
    second_demand_id = uuid4()
    shared_employee_id = uuid4()
    first_only_employee_id = uuid4()
    second_only_employee_id = uuid4()
    deadline = datetime(2026, 9, 20, tzinfo=UTC)
    problem = OptimizationProblem(
        operation_id=operation_id,
        mobilization_deadline=deadline,
        demands=(
            Demand(first_demand_id, required_headcount=1),
            Demand(second_demand_id, required_headcount=1),
        ),
        candidates=(
            Candidate(shared_employee_id, first_demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(shared_employee_id, second_demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(first_only_employee_id, first_demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(second_only_employee_id, second_demand_id, EligibilityStatus.ELIGIBLE),
        ),
    )

    built = build_assignment_model(problem)
    solver = cp_model.CpSolver()
    status = solver.Solve(built.model)
    selected = [
        key for key, variable in built.assignment_variables.items() if solver.Value(variable)
    ]

    assert status in {cp_model.OPTIMAL, cp_model.FEASIBLE}
    assert sum(key.demand_id == first_demand_id for key in selected) == 1
    assert sum(key.demand_id == second_demand_id for key in selected) == 1
    assert len({key.employee_id for key in selected}) == 2


def test_ineligible_candidate_is_never_exposed_as_an_assignment_variable() -> None:
    demand_id = uuid4()
    eligible_employee_id = uuid4()
    ineligible_employee_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(eligible_employee_id, demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(ineligible_employee_id, demand_id, EligibilityStatus.INELIGIBLE),
        ),
    )

    built = build_assignment_model(problem)

    assert CandidateKey(eligible_employee_id, demand_id) in built.assignment_variables
    assert CandidateKey(ineligible_employee_id, demand_id) not in built.assignment_variables


def test_selected_trainable_candidate_activates_required_training() -> None:
    demand_id = uuid4()
    employee_id = uuid4()
    training_catalog_id = uuid4()
    deadline = datetime(2026, 9, 20, tzinfo=UTC)
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=deadline,
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(
                employee_id,
                demand_id,
                EligibilityStatus.TRAINABLE,
                required_training=(
                    TrainingAction(
                        training_catalog_id,
                        datetime(2026, 9, 19, tzinfo=UTC),
                        cost_cents=50_000,
                    ),
                ),
                incremental_cost_cents=120_000,
            ),
        ),
    )

    built = build_assignment_model(problem)
    solver = cp_model.CpSolver()
    status = solver.Solve(built.model)

    assert status in {cp_model.OPTIMAL, cp_model.FEASIBLE}
    assert solver.Value(built.assignment_variables[CandidateKey(employee_id, demand_id)]) == 1
    assert (
        solver.Value(built.training_variables[TrainingKey(employee_id, training_catalog_id)]) == 1
    )
    assert solver.Value(built.metrics.assignment_cost_cents) == 120_000
    assert solver.Value(built.metrics.training_cost_cents) == 50_000
    assert solver.Value(built.metrics.total_incremental_cost_cents) == 170_000
    assert solver.Value(built.metrics.training_count) == 1


def test_explicitly_conflicting_candidates_cannot_both_be_selected() -> None:
    demand_id = uuid4()
    first_employee_id = uuid4()
    second_employee_id = uuid4()
    first_key = CandidateKey(first_employee_id, demand_id)
    second_key = CandidateKey(second_employee_id, demand_id)
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=2),),
        candidates=(
            Candidate(first_employee_id, demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(second_employee_id, demand_id, EligibilityStatus.ELIGIBLE),
        ),
        conflicting_candidate_pairs=((first_key, second_key),),
    )

    built = build_assignment_model(problem)
    status = cp_model.CpSolver().Solve(built.model)

    assert status == cp_model.INFEASIBLE


def test_fixed_seed_random_models_preserve_coverage_and_uniqueness() -> None:
    deadline = datetime(2026, 9, 20, tzinfo=UTC)
    for seed in range(10):
        rng = random.Random(seed)
        demand_ids = [uuid4() for _ in range(3)]
        employee_ids = [uuid4() for _ in range(8)]
        candidates: dict[CandidateKey, Candidate] = {}
        for index, demand_id in enumerate(demand_ids):
            employee_id = employee_ids[index]
            candidates[CandidateKey(employee_id, demand_id)] = Candidate(
                employee_id,
                demand_id,
                EligibilityStatus.ELIGIBLE,
            )
        for employee_id in employee_ids:
            for demand_id in demand_ids:
                if rng.random() < 0.45:
                    key = CandidateKey(employee_id, demand_id)
                    candidates.setdefault(
                        key,
                        Candidate(employee_id, demand_id, EligibilityStatus.ELIGIBLE),
                    )
        problem = OptimizationProblem(
            operation_id=uuid4(),
            mobilization_deadline=deadline,
            demands=tuple(Demand(demand_id, required_headcount=1) for demand_id in demand_ids),
            candidates=tuple(candidates.values()),
        )

        built = build_assignment_model(problem)
        solver = cp_model.CpSolver()
        status = solver.Solve(built.model)
        selected = [
            key for key, variable in built.assignment_variables.items() if solver.Value(variable)
        ]

        assert status in {cp_model.OPTIMAL, cp_model.FEASIBLE}
        assert all(
            sum(key.demand_id == demand_id for key in selected) == 1 for demand_id in demand_ids
        )
        assert len({key.employee_id for key in selected}) == len(selected)
