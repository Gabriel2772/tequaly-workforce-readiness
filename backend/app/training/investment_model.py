from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from ortools.sat.python import cp_model

from app.optimization.types import OptimizationStatus


@dataclass(frozen=True)
class InvestmentOpportunity:
    employee_id: UUID
    qualification_id: UUID
    training_catalog_id: UUID
    training_session_id: UUID
    completes_at: datetime
    cost_cents: int
    coverage_gain: int
    unlocked_position_count: int
    benefited_operation_ids: tuple[UUID, ...]
    benefited_demand_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class InvestmentProblem:
    budget_cents: int
    opportunities: tuple[InvestmentOpportunity, ...]
    session_capacities: tuple[tuple[UUID, int], ...] = ()
    demand_capacities: tuple[tuple[UUID, int], ...] = ()
    session_periods: tuple[tuple[UUID, datetime, datetime], ...] = ()


@dataclass(frozen=True)
class InvestmentResult:
    status: OptimizationStatus
    selected: tuple[InvestmentOpportunity, ...]
    total_cost_cents: int
    coverage_gain: int
    unlocked_position_count: int
    runtime_ms: int


@dataclass(frozen=True)
class _Priority:
    sense: str
    expression: cp_model.LinearExprT


def _epoch_minutes(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() // 60)


def solve_investment(
    problem: InvestmentProblem,
    *,
    time_limit_seconds: float = 30.0,
) -> InvestmentResult:
    started_at = perf_counter()
    ordered = tuple(
        sorted(
            problem.opportunities,
            key=lambda item: (
                str(item.employee_id),
                str(item.qualification_id),
                item.completes_at,
                item.cost_cents,
                str(item.training_session_id),
            ),
        )
    )
    model = cp_model.CpModel()
    selected_variables = [
        model.new_bool_var(f"investment_{index}") for index in range(len(ordered))
    ]
    model.add(
        cp_model.LinearExpr.sum([
            opportunity.cost_cents * variable
            for opportunity, variable in zip(ordered, selected_variables, strict=True)
        ])
        <= problem.budget_cents
    )

    pair_indexes: dict[tuple[UUID, UUID], list[int]] = {}
    session_indexes: dict[UUID, list[int]] = {}
    for index, opportunity in enumerate(ordered):
        pair_indexes.setdefault(
            (opportunity.employee_id, opportunity.qualification_id), []
        ).append(index)
        session_indexes.setdefault(opportunity.training_session_id, []).append(index)
    for indexes in pair_indexes.values():
        model.add(sum(selected_variables[index] for index in indexes) <= 1)
    periods = {
        session_id: (starts_at, ends_at)
        for session_id, starts_at, ends_at in problem.session_periods
    }
    employee_indexes: dict[UUID, list[int]] = {}
    for index, opportunity in enumerate(ordered):
        employee_indexes.setdefault(opportunity.employee_id, []).append(index)
    for indexes in employee_indexes.values():
        for position, first_index in enumerate(indexes):
            first_period = periods.get(ordered[first_index].training_session_id)
            if first_period is None:
                continue
            for second_index in indexes[position + 1 :]:
                second_period = periods.get(ordered[second_index].training_session_id)
                if second_period is None:
                    continue
                if (
                    first_period[0] < second_period[1]
                    and first_period[1] > second_period[0]
                ):
                    model.add(
                        selected_variables[first_index]
                        + selected_variables[second_index]
                        <= 1
                    )
    capacities = dict(problem.session_capacities)
    for session_id, indexes in session_indexes.items():
        if session_id in capacities:
            model.add(
                sum(selected_variables[index] for index in indexes)
                <= capacities[session_id]
            )

    demand_capacities = dict(problem.demand_capacities)
    for demand_id, capacity in demand_capacities.items():
        indexes = [
            index
            for index, opportunity in enumerate(ordered)
            if demand_id in opportunity.benefited_demand_ids
        ]
        if indexes:
            model.add(sum(selected_variables[index] for index in indexes) <= capacity)

    coverage = cp_model.LinearExpr.sum([
        opportunity.coverage_gain * variable
        for opportunity, variable in zip(ordered, selected_variables, strict=True)
    ])
    cost = cp_model.LinearExpr.sum([
        opportunity.cost_cents * variable
        for opportunity, variable in zip(ordered, selected_variables, strict=True)
    ])
    completion = cp_model.LinearExpr.sum([
        _epoch_minutes(opportunity.completes_at) * variable
        for opportunity, variable in zip(ordered, selected_variables, strict=True)
    ])
    action_count = cp_model.LinearExpr.sum(selected_variables)
    stable_tie_break = cp_model.LinearExpr.sum([
        (index + 1) * variable for index, variable in enumerate(selected_variables)
    ])
    priorities = (
        _Priority("max", coverage),
        _Priority("min", cost),
        _Priority("min", completion),
        _Priority("min", action_count),
        _Priority("min", stable_tie_break),
    )

    solver: cp_model.CpSolver | None = None
    final_status = OptimizationStatus.OPTIMAL
    for priority in priorities:
        remaining = time_limit_seconds - (perf_counter() - started_at)
        if remaining <= 0:
            final_status = (
                OptimizationStatus.TIMEOUT
                if solver is None
                else OptimizationStatus.TIMEOUT_FEASIBLE
            )
            break
        if priority.sense == "max":
            model.maximize(priority.expression)
        else:
            model.minimize(priority.expression)
        stage_solver = cp_model.CpSolver()
        stage_solver.parameters.max_time_in_seconds = remaining
        stage_solver.parameters.num_search_workers = 1
        stage_solver.parameters.random_seed = 0
        status = stage_solver.solve(model)
        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            return InvestmentResult(
                status=(
                    OptimizationStatus.INFEASIBLE
                    if status == cp_model.INFEASIBLE
                    else OptimizationStatus.ERROR
                    if status == cp_model.MODEL_INVALID
                    else OptimizationStatus.TIMEOUT
                ),
                selected=(),
                total_cost_cents=0,
                coverage_gain=0,
                unlocked_position_count=0,
                runtime_ms=round((perf_counter() - started_at) * 1000),
            )
        solver = stage_solver
        if status == cp_model.FEASIBLE:
            final_status = OptimizationStatus.TIMEOUT_FEASIBLE
            break
        model.add(priority.expression == solver.value(priority.expression))

    if solver is None:
        chosen: tuple[InvestmentOpportunity, ...] = ()
    else:
        chosen = tuple(
            opportunity
            for opportunity, variable in zip(ordered, selected_variables, strict=True)
            if solver.value(variable)
        )
    return InvestmentResult(
        status=final_status,
        selected=chosen,
        total_cost_cents=sum(item.cost_cents for item in chosen),
        coverage_gain=sum(item.coverage_gain for item in chosen),
        unlocked_position_count=sum(item.unlocked_position_count for item in chosen),
        runtime_ms=round((perf_counter() - started_at) * 1000),
    )
