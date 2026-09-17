from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.decisions.models import (
    AuditEvent,
    DecisionAssignment,
    DecisionRun,
    DecisionTrainingAction,
)
from app.optimization.schemas import (
    OptimizationAssignmentView,
    OptimizationBlockerView,
    OptimizationResultView,
    OptimizationTrainingView,
)
from app.optimization.types import (
    Candidate,
    CandidateKey,
    Objective,
    SolvedOptimization,
    TrainingAction,
    TrainingKey,
)


class DecisionPersistenceService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def persist(
        self,
        *,
        operation_id: UUID,
        operation_starts_at: datetime,
        operation_ends_at: datetime,
        objective: Objective,
        solution: SolvedOptimization,
        candidates: dict[CandidateKey, Candidate],
        training_actions: dict[TrainingKey, TrainingAction],
        solver_version: str,
        rules_version: str,
        input_snapshot_hash: str,
        eligibility_run_id: UUID,
    ) -> OptimizationResultView:
        blocker_views = [
            OptimizationBlockerView(
                code=blocker.code,
                demand_id=blocker.demand_id,
                required_headcount=blocker.required_headcount,
                available_candidates=blocker.available_candidates,
                uncovered_headcount=blocker.uncovered_headcount,
                blocking_requirement_ids=list(blocker.blocking_requirement_ids),
                affected_demand_ids=list(blocker.affected_demand_ids),
            )
            for blocker in solution.blockers
        ]
        blockers = [blocker.model_dump(mode="json") for blocker in blocker_views]
        candidate_snapshot = [
            {
                "employee_id": str(key.employee_id),
                "demand_id": str(key.demand_id),
                "status": candidate.status.value,
                "incremental_cost_cents": candidate.incremental_cost_cents,
                "ready_at": candidate.ready_at.isoformat() if candidate.ready_at else None,
                "internal": candidate.internal,
                "utilization_score": candidate.utilization_score,
                "required_training_ids": [
                    str(action.training_catalog_id) for action in candidate.required_training
                ],
            }
            for key, candidate in sorted(candidates.items(), key=lambda item: str(item[0]))
        ]
        metrics: dict[str, object] = {
            **solution.metrics,
            "blockers": blockers,
            "eligibility_run_id": str(eligibility_run_id),
            "candidate_count": len(candidates),
        }
        run = DecisionRun(
            operation_id=operation_id,
            objective=objective.value,
            solver_version=solver_version,
            rules_version=rules_version,
            input_snapshot_hash=input_snapshot_hash,
            status=solution.status.value,
            runtime_ms=solution.runtime_ms,
            metrics=metrics,
            candidate_snapshot=candidate_snapshot,
            created_by=self._actor_id,
        )
        self._session.add(run)
        self._session.flush()

        assignment_views: list[OptimizationAssignmentView] = []
        for key in solution.assignment_keys:
            candidate = candidates[key]
            record = DecisionAssignment(
                decision_run_id=run.id,
                employee_id=key.employee_id,
                role_demand_id=key.demand_id,
                starts_at=operation_starts_at,
                ends_at=operation_ends_at,
                incremental_cost_cents=candidate.incremental_cost_cents,
            )
            self._session.add(record)
            assignment_views.append(
                OptimizationAssignmentView(
                    employee_id=key.employee_id,
                    demand_id=key.demand_id,
                    starts_at=operation_starts_at,
                    ends_at=operation_ends_at,
                    incremental_cost_cents=candidate.incremental_cost_cents,
                )
            )

        training_views: list[OptimizationTrainingView] = []
        for training_key in solution.training_keys:
            action = training_actions[training_key]
            self._session.add(
                DecisionTrainingAction(
                    decision_run_id=run.id,
                    employee_id=training_key.employee_id,
                    training_catalog_id=training_key.training_catalog_id,
                    ready_at=action.completes_at,
                    cost_cents=action.cost_cents,
                    duration_minutes=action.duration_minutes,
                )
            )
            training_views.append(
                OptimizationTrainingView(
                    employee_id=training_key.employee_id,
                    training_catalog_id=training_key.training_catalog_id,
                    ready_at=action.completes_at,
                    cost_cents=action.cost_cents,
                    duration_minutes=action.duration_minutes,
                )
            )

        occurred_at = datetime.now(UTC)
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="decision.run_completed",
                aggregate_type="operation",
                aggregate_id=operation_id,
                payload={
                    "decision_run_id": str(run.id),
                    "objective": objective.value,
                    "status": solution.status.value,
                    "assignment_count": len(assignment_views),
                    "training_count": len(training_views),
                    "runtime_ms": solution.runtime_ms,
                },
                occurred_at=occurred_at,
            )
        )
        self._session.flush()
        return OptimizationResultView(
            id=run.id,
            operation_id=operation_id,
            objective=objective,
            status=solution.status,
            solver_version=solver_version,
            rules_version=rules_version,
            input_snapshot_hash=input_snapshot_hash,
            runtime_ms=solution.runtime_ms,
            metrics=metrics,
            assignments=assignment_views,
            training=training_views,
            blockers=blocker_views,
            created_by=self._actor_id,
            created_at=run.created_at,
        )
