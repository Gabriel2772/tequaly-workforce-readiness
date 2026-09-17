from ortools.sat.python import cp_model

from app.optimization.constraints import (
    add_demand_coverage,
    add_employee_uniqueness,
    add_explicit_conflicts,
    add_required_training,
    candidate_satisfies_hard_guards,
    precheck_problem,
)
from app.optimization.types import (
    BuiltModel,
    Candidate,
    CandidateKey,
    ModelMetrics,
    OptimizationProblem,
    TrainingAction,
    TrainingKey,
)


def _sum(expressions: list[cp_model.LinearExprT]) -> cp_model.LinearExprT:
    return cp_model.LinearExpr.sum(expressions)


def _build_metrics(
    candidates: dict[CandidateKey, Candidate],
    assignment_variables: dict[CandidateKey, cp_model.IntVar],
    training_variables: dict[TrainingKey, cp_model.IntVar],
    training_actions: dict[TrainingKey, TrainingAction],
) -> ModelMetrics:
    assignment_cost = _sum(
        [
            assignment_variables[key] * candidate.incremental_cost_cents
            for key, candidate in candidates.items()
        ]
    )
    training_cost = _sum(
        [training_variables[key] * action.cost_cents for key, action in training_actions.items()]
    )
    return ModelMetrics(
        assignment_cost_cents=assignment_cost,
        training_cost_cents=training_cost,
        total_incremental_cost_cents=_sum([assignment_cost, training_cost]),
        training_count=_sum(list(training_variables.values())),
        training_minutes=_sum(
            [
                training_variables[key] * action.duration_minutes
                for key, action in training_actions.items()
            ]
        ),
        internal_assignment_count=_sum(
            [
                assignment_variables[key]
                for key, candidate in candidates.items()
                if candidate.internal
            ]
        ),
        qualified_assignment_count=_sum(
            [
                assignment_variables[key]
                for key, candidate in candidates.items()
                if candidate.status.value == "ELIGIBLE"
            ]
        ),
        utilization_score=_sum(
            [
                assignment_variables[key] * candidate.utilization_score
                for key, candidate in candidates.items()
            ]
        ),
        readiness_epoch_minutes={
            key: int(candidate.ready_at.timestamp() // 60) if candidate.ready_at else 0
            for key, candidate in candidates.items()
        },
    )


def build_assignment_model(problem: OptimizationProblem) -> BuiltModel:
    diagnostics = precheck_problem(problem)
    model = cp_model.CpModel()
    allowed_candidates: dict[CandidateKey, Candidate] = {}
    assignment_variables: dict[CandidateKey, cp_model.IntVar] = {}

    for candidate in problem.candidates:
        if not candidate_satisfies_hard_guards(candidate, problem.mobilization_deadline):
            continue
        key = CandidateKey(candidate.employee_id, candidate.demand_id)
        variable = model.new_bool_var(f"assign_{candidate.employee_id}_{candidate.demand_id}")
        allowed_candidates[key] = candidate
        assignment_variables[key] = variable
    add_demand_coverage(model, problem.demands, assignment_variables)
    add_employee_uniqueness(model, assignment_variables)
    add_explicit_conflicts(
        model,
        problem.conflicting_candidate_pairs,
        assignment_variables,
    )
    training_variables, training_actions = add_required_training(
        model, allowed_candidates, assignment_variables
    )
    metrics = _build_metrics(
        allowed_candidates,
        assignment_variables,
        training_variables,
        training_actions,
    )

    return BuiltModel(
        model=model,
        assignment_variables=assignment_variables,
        training_variables=training_variables,
        candidates=allowed_candidates,
        training_actions=training_actions,
        diagnostics=diagnostics,
        metrics=metrics,
    )
