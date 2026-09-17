from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ortools.sat.python import cp_model

from app.eligibility.types import EligibilityStatus


class Objective(StrEnum):
    MIN_COST = "MIN_COST"
    FASTEST_READY = "FASTEST_READY"
    MAX_INTERNAL = "MAX_INTERNAL"


class OptimizationStatus(StrEnum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    TIMEOUT = "TIMEOUT"
    TIMEOUT_FEASIBLE = "TIMEOUT_FEASIBLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Demand:
    demand_id: UUID
    required_headcount: int
    blocking_requirement_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class TrainingAction:
    training_catalog_id: UUID
    completes_at: datetime
    cost_cents: int = 0
    duration_minutes: int = 0


@dataclass(frozen=True)
class Candidate:
    employee_id: UUID
    demand_id: UUID
    status: EligibilityStatus
    required_training: tuple[TrainingAction, ...] = ()
    incremental_cost_cents: int = 0
    ready_at: datetime | None = None
    internal: bool = True
    utilization_score: int = 0


@dataclass(frozen=True)
class CandidateKey:
    employee_id: UUID
    demand_id: UUID


@dataclass(frozen=True)
class TrainingKey:
    employee_id: UUID
    training_catalog_id: UUID


@dataclass(frozen=True)
class OptimizationProblem:
    operation_id: UUID
    mobilization_deadline: datetime
    demands: tuple[Demand, ...]
    candidates: tuple[Candidate, ...]
    conflicting_candidate_pairs: tuple[tuple[CandidateKey, CandidateKey], ...] = ()


@dataclass(frozen=True)
class InfeasibilityDiagnostic:
    code: str
    demand_id: UUID | None
    required_headcount: int
    available_candidates: int
    uncovered_headcount: int
    blocking_requirement_ids: tuple[UUID, ...] = ()
    affected_demand_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class ModelMetrics:
    assignment_cost_cents: cp_model.LinearExprT
    training_cost_cents: cp_model.LinearExprT
    total_incremental_cost_cents: cp_model.LinearExprT
    training_count: cp_model.LinearExprT
    training_minutes: cp_model.LinearExprT
    internal_assignment_count: cp_model.LinearExprT
    qualified_assignment_count: cp_model.LinearExprT
    utilization_score: cp_model.LinearExprT
    readiness_epoch_minutes: dict[CandidateKey, int]


@dataclass(frozen=True)
class BuiltModel:
    model: cp_model.CpModel
    assignment_variables: dict[CandidateKey, cp_model.IntVar]
    training_variables: dict[TrainingKey, cp_model.IntVar]
    candidates: dict[CandidateKey, Candidate]
    training_actions: dict[TrainingKey, TrainingAction]
    diagnostics: tuple[InfeasibilityDiagnostic, ...]
    metrics: ModelMetrics


@dataclass(frozen=True)
class SolvedOptimization:
    status: OptimizationStatus
    objective: Objective
    assignment_keys: tuple[CandidateKey, ...]
    training_keys: tuple[TrainingKey, ...]
    metrics: dict[str, int]
    blockers: tuple[InfeasibilityDiagnostic, ...]
    runtime_ms: int
