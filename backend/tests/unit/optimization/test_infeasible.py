from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from ortools.sat.python import cp_model

from app.eligibility.types import EligibilityStatus
from app.optimization.constraints import precheck_problem
from app.optimization.model_builder import build_assignment_model
from app.optimization.types import (
    Candidate,
    CandidateKey,
    Demand,
    OptimizationProblem,
    TrainingAction,
)


def test_precheck_reports_uncovered_headcount_and_blocking_requirements() -> None:
    demand_id = uuid4()
    requirement_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(
            Demand(
                demand_id,
                required_headcount=2,
                blocking_requirement_ids=(requirement_id,),
            ),
        ),
        candidates=(Candidate(uuid4(), demand_id, EligibilityStatus.ELIGIBLE),),
    )

    diagnostics = precheck_problem(problem)

    assert diagnostics[0].code == "insufficient_candidates"
    assert diagnostics[0].demand_id == demand_id
    assert diagnostics[0].required_headcount == 2
    assert diagnostics[0].available_candidates == 1
    assert diagnostics[0].uncovered_headcount == 1
    assert diagnostics[0].blocking_requirement_ids == (requirement_id,)


def test_training_after_deadline_is_excluded_and_model_is_infeasible() -> None:
    demand_id = uuid4()
    employee_id = uuid4()
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
                required_training=(TrainingAction(uuid4(), deadline + timedelta(seconds=1)),),
            ),
        ),
    )

    built = build_assignment_model(problem)
    status = cp_model.CpSolver().Solve(built.model)

    assert CandidateKey(employee_id, demand_id) not in built.assignment_variables
    assert status == cp_model.INFEASIBLE
    assert built.diagnostics[0].uncovered_headcount == 1


def test_global_precheck_detects_one_employee_needed_by_two_demands() -> None:
    employee_id = uuid4()
    first_demand_id = uuid4()
    second_demand_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(
            Demand(first_demand_id, required_headcount=1),
            Demand(second_demand_id, required_headcount=1),
        ),
        candidates=(
            Candidate(employee_id, first_demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(employee_id, second_demand_id, EligibilityStatus.ELIGIBLE),
        ),
    )

    diagnostics = precheck_problem(problem)

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "workforce_capacity_shortfall"
    assert diagnostics[0].uncovered_headcount == 1


def test_duplicate_candidate_keys_are_rejected_before_model_creation() -> None:
    demand_id = uuid4()
    employee_id = uuid4()
    duplicate = Candidate(employee_id, demand_id, EligibilityStatus.ELIGIBLE)
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(duplicate, duplicate),
    )

    with pytest.raises(ValueError, match="duplicate candidate"):
        build_assignment_model(problem)
