from dataclasses import dataclass
from time import perf_counter

from ortools.sat.python import cp_model

from app.optimization.model_builder import build_assignment_model
from app.optimization.types import (
    BuiltModel,
    Objective,
    OptimizationProblem,
    OptimizationStatus,
    SolvedOptimization,
)


@dataclass(frozen=True)
class _Priority:
    sense: str
    expression: cp_model.LinearExprT


def _team_ready_variable(built: BuiltModel) -> cp_model.IntVar:
    upper_bound = max(built.metrics.readiness_epoch_minutes.values(), default=0)
    team_ready = built.model.new_int_var(0, upper_bound, "team_ready_at_epoch_minutes")
    readiness_expressions = [
        built.metrics.readiness_epoch_minutes[key] * assignment
        for key, assignment in built.assignment_variables.items()
    ]
    if readiness_expressions:
        built.model.add_max_equality(team_ready, readiness_expressions)
    else:
        built.model.add(team_ready == 0)
    return team_ready


def _tie_break_expression(built: BuiltModel) -> cp_model.LinearExprT:
    ranked_variables = [
        variable * rank
        for rank, (_key, variable) in enumerate(
            sorted(built.assignment_variables.items(), key=lambda item: str(item[0])),
            start=1,
        )
    ]
    return cp_model.LinearExpr.sum(ranked_variables)


def _priorities(
    built: BuiltModel,
    objective: Objective,
    team_ready: cp_model.IntVar,
) -> tuple[_Priority, ...]:
    tie_break = _tie_break_expression(built)
    if objective is Objective.MIN_COST:
        return (
            _Priority("min", built.metrics.total_incremental_cost_cents),
            _Priority("min", team_ready),
            _Priority("min", built.metrics.training_count),
            _Priority("min", tie_break),
        )
    if objective is Objective.FASTEST_READY:
        return (
            _Priority("min", team_ready),
            _Priority("min", built.metrics.training_count),
            _Priority("min", built.metrics.total_incremental_cost_cents),
            _Priority("min", tie_break),
        )
    return (
        _Priority("max", built.metrics.internal_assignment_count),
        _Priority("max", built.metrics.qualified_assignment_count),
        _Priority("max", built.metrics.utilization_score),
        _Priority("min", built.metrics.training_minutes),
        _Priority("min", built.metrics.total_incremental_cost_cents),
        _Priority("min", tie_break),
    )


def _empty_result(
    objective: Objective,
    status: OptimizationStatus,
    built: BuiltModel,
    started_at: float,
) -> SolvedOptimization:
    return SolvedOptimization(
        status=status,
        objective=objective,
        assignment_keys=(),
        training_keys=(),
        metrics={},
        blockers=built.diagnostics,
        runtime_ms=round((perf_counter() - started_at) * 1000),
    )


def _solution_result(
    objective: Objective,
    status: OptimizationStatus,
    built: BuiltModel,
    solver: cp_model.CpSolver,
    team_ready: cp_model.IntVar,
    started_at: float,
) -> SolvedOptimization:
    assignments = tuple(
        key
        for key, variable in sorted(
            built.assignment_variables.items(), key=lambda item: str(item[0])
        )
        if solver.value(variable)
    )
    training = tuple(
        key
        for key, variable in sorted(built.training_variables.items(), key=lambda item: str(item[0]))
        if solver.value(variable)
    )
    return SolvedOptimization(
        status=status,
        objective=objective,
        assignment_keys=assignments,
        training_keys=training,
        metrics={
            "assignment_cost_cents": solver.value(built.metrics.assignment_cost_cents),
            "training_cost_cents": solver.value(built.metrics.training_cost_cents),
            "total_incremental_cost_cents": solver.value(
                built.metrics.total_incremental_cost_cents
            ),
            "training_count": solver.value(built.metrics.training_count),
            "training_minutes": solver.value(built.metrics.training_minutes),
            "internal_assignment_count": solver.value(built.metrics.internal_assignment_count),
            "qualified_assignment_count": solver.value(built.metrics.qualified_assignment_count),
            "utilization_score": solver.value(built.metrics.utilization_score),
            "team_ready_at_epoch_minutes": solver.value(team_ready),
        },
        blockers=(),
        runtime_ms=round((perf_counter() - started_at) * 1000),
    )


def solve_problem(
    problem: OptimizationProblem,
    objective: Objective,
    *,
    time_limit_seconds: float = 30.0,
) -> SolvedOptimization:
    started_at = perf_counter()
    built = build_assignment_model(problem)
    if built.diagnostics:
        return _empty_result(
            objective,
            OptimizationStatus.INFEASIBLE,
            built,
            started_at,
        )

    team_ready = _team_ready_variable(built)
    solver: cp_model.CpSolver | None = None
    for priority in _priorities(built, objective, team_ready):
        remaining_seconds = time_limit_seconds - (perf_counter() - started_at)
        if remaining_seconds <= 0:
            if solver is None:
                return _empty_result(
                    objective,
                    OptimizationStatus.TIMEOUT,
                    built,
                    started_at,
                )
            return _solution_result(
                objective,
                OptimizationStatus.TIMEOUT_FEASIBLE,
                built,
                solver,
                team_ready,
                started_at,
            )
        if priority.sense == "min":
            built.model.minimize(priority.expression)
        else:
            built.model.maximize(priority.expression)
        stage_solver = cp_model.CpSolver()
        stage_solver.parameters.max_time_in_seconds = remaining_seconds
        stage_solver.parameters.num_search_workers = 1
        stage_solver.parameters.random_seed = 0
        stage_status = stage_solver.solve(built.model)
        if stage_status == cp_model.INFEASIBLE:
            return _empty_result(
                objective,
                OptimizationStatus.INFEASIBLE,
                built,
                started_at,
            )
        if stage_status == cp_model.MODEL_INVALID:
            return _empty_result(
                objective,
                OptimizationStatus.ERROR,
                built,
                started_at,
            )
        if stage_status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            return _empty_result(
                objective,
                OptimizationStatus.TIMEOUT,
                built,
                started_at,
            )
        solver = stage_solver
        if stage_status == cp_model.FEASIBLE:
            return _solution_result(
                objective,
                OptimizationStatus.TIMEOUT_FEASIBLE,
                built,
                solver,
                team_ready,
                started_at,
            )
        optimum = solver.value(priority.expression)
        built.model.add(priority.expression == optimum)

    assert solver is not None
    return _solution_result(
        objective,
        OptimizationStatus.OPTIMAL,
        built,
        solver,
        team_ready,
        started_at,
    )
