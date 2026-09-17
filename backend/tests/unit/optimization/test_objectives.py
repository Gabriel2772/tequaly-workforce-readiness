from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.eligibility.types import EligibilityStatus
from app.optimization.objectives import solve_problem
from app.optimization.types import (
    Candidate,
    Demand,
    Objective,
    OptimizationProblem,
    TrainingAction,
)


def test_min_cost_selects_the_cheapest_feasible_team() -> None:
    demand_id = uuid4()
    cheap_employee_id = uuid4()
    expensive_employee_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(
                cheap_employee_id,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=100_00,
            ),
            Candidate(
                expensive_employee_id,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=200_00,
            ),
        ),
    )

    result = solve_problem(problem, Objective.MIN_COST)

    assert result.status == "OPTIMAL"
    assert result.assignment_keys[0].employee_id == cheap_employee_id
    assert result.metrics["total_incremental_cost_cents"] == 100_00


def test_fastest_ready_minimizes_the_latest_selected_readiness() -> None:
    demand_id = uuid4()
    early_employee_id = uuid4()
    late_employee_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(
                early_employee_id,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=500_00,
                ready_at=datetime(2026, 9, 10, tzinfo=UTC),
            ),
            Candidate(
                late_employee_id,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=100_00,
                ready_at=datetime(2026, 9, 19, tzinfo=UTC),
            ),
        ),
    )

    result = solve_problem(problem, Objective.FASTEST_READY)

    assert result.status == "OPTIMAL"
    assert result.assignment_keys[0].employee_id == early_employee_id
    assert result.metrics["team_ready_at_epoch_minutes"] == int(
        datetime(2026, 9, 10, tzinfo=UTC).timestamp() // 60
    )


def test_max_internal_prefers_qualified_internal_and_then_utilization() -> None:
    demand_id = uuid4()
    qualified_high_utilization = uuid4()
    qualified_low_utilization = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(
                uuid4(),
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=1,
                internal=False,
                utilization_score=100,
            ),
            Candidate(
                uuid4(),
                demand_id,
                EligibilityStatus.TRAINABLE,
                required_training=(TrainingAction(uuid4(), datetime(2026, 9, 19, tzinfo=UTC)),),
                internal=True,
                utilization_score=100,
            ),
            Candidate(
                qualified_low_utilization,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=1,
                internal=True,
                utilization_score=20,
            ),
            Candidate(
                qualified_high_utilization,
                demand_id,
                EligibilityStatus.ELIGIBLE,
                incremental_cost_cents=999_00,
                internal=True,
                utilization_score=80,
            ),
        ),
    )

    result = solve_problem(problem, Objective.MAX_INTERNAL)

    assert result.status == "OPTIMAL"
    assert result.assignment_keys[0].employee_id == qualified_high_utilization
    assert result.metrics["internal_assignment_count"] == 1
    assert result.metrics["qualified_assignment_count"] == 1
    assert result.metrics["utilization_score"] == 80


def test_exact_ties_have_a_stable_candidate_key_tie_break() -> None:
    demand_id = UUID(int=99)
    first_employee_id = UUID(int=1)
    second_employee_id = UUID(int=2)
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(second_employee_id, demand_id, EligibilityStatus.ELIGIBLE),
            Candidate(first_employee_id, demand_id, EligibilityStatus.ELIGIBLE),
        ),
    )

    selected = {
        solve_problem(problem, Objective.MIN_COST).assignment_keys[0].employee_id for _ in range(3)
    }

    assert selected == {first_employee_id}


def test_max_internal_minimizes_training_minutes_before_cost() -> None:
    demand_id = uuid4()
    shorter_training_employee = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(
            Candidate(
                shorter_training_employee,
                demand_id,
                EligibilityStatus.TRAINABLE,
                required_training=(
                    TrainingAction(
                        uuid4(),
                        datetime(2026, 9, 19, tzinfo=UTC),
                        cost_cents=500_00,
                        duration_minutes=60,
                    ),
                ),
                utilization_score=50,
            ),
            Candidate(
                uuid4(),
                demand_id,
                EligibilityStatus.TRAINABLE,
                required_training=(
                    TrainingAction(
                        uuid4(),
                        datetime(2026, 9, 19, tzinfo=UTC),
                        cost_cents=1,
                        duration_minutes=120,
                    ),
                ),
                utilization_score=50,
            ),
        ),
    )

    result = solve_problem(problem, Objective.MAX_INTERNAL)

    assert result.assignment_keys[0].employee_id == shorter_training_employee
    assert result.metrics["training_minutes"] == 60


def test_zero_time_budget_returns_explicit_timeout() -> None:
    demand_id = uuid4()
    problem = OptimizationProblem(
        operation_id=uuid4(),
        mobilization_deadline=datetime(2026, 9, 20, tzinfo=UTC),
        demands=(Demand(demand_id, required_headcount=1),),
        candidates=(Candidate(uuid4(), demand_id, EligibilityStatus.ELIGIBLE),),
    )

    result = solve_problem(
        problem,
        Objective.MIN_COST,
        time_limit_seconds=0,
    )

    assert result.status == "TIMEOUT"
    assert result.assignment_keys == ()


def test_precheck_infeasibility_is_returned_with_blockers() -> None:
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

    result = solve_problem(problem, Objective.MIN_COST)

    assert result.status == "INFEASIBLE"
    assert result.blockers[0].demand_id == demand_id
    assert result.blockers[0].blocking_requirement_ids == (requirement_id,)
