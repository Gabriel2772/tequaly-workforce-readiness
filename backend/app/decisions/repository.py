from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decisions.models import (
    DecisionAssignment,
    DecisionRun,
    DecisionTrainingAction,
)
from app.optimization.schemas import (
    OptimizationAssignmentView,
    OptimizationBlockerView,
    OptimizationResultView,
    OptimizationTrainingView,
    ScenarioCollection,
)
from app.optimization.types import Objective, OptimizationStatus


class DecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_scenarios(self, operation_id: UUID) -> ScenarioCollection:
        runs = tuple(
            self._session.scalars(
                select(DecisionRun)
                .where(DecisionRun.operation_id == operation_id)
                .order_by(DecisionRun.created_at.desc(), DecisionRun.id)
            )
        )
        return ScenarioCollection(items=[self.to_view(run) for run in runs])

    def list_all(self) -> ScenarioCollection:
        runs = tuple(
            self._session.scalars(
                select(DecisionRun).order_by(DecisionRun.created_at.desc(), DecisionRun.id)
            )
        )
        return ScenarioCollection(items=[self.to_view(run) for run in runs])

    def get(self, decision_run_id: UUID) -> OptimizationResultView | None:
        run = self._session.get(DecisionRun, decision_run_id)
        return self.to_view(run) if run is not None else None

    def to_view(self, run: DecisionRun) -> OptimizationResultView:
        assignments = tuple(
            self._session.scalars(
                select(DecisionAssignment)
                .where(DecisionAssignment.decision_run_id == run.id)
                .order_by(DecisionAssignment.role_demand_id, DecisionAssignment.employee_id)
            )
        )
        training = tuple(
            self._session.scalars(
                select(DecisionTrainingAction)
                .where(DecisionTrainingAction.decision_run_id == run.id)
                .order_by(
                    DecisionTrainingAction.ready_at,
                    DecisionTrainingAction.employee_id,
                )
            )
        )
        raw_blockers = run.metrics.get("blockers", [])
        blockers = raw_blockers if isinstance(raw_blockers, list) else []
        return OptimizationResultView(
            id=run.id,
            operation_id=run.operation_id,
            objective=Objective(run.objective),
            status=OptimizationStatus(run.status),
            solver_version=run.solver_version,
            rules_version=run.rules_version,
            input_snapshot_hash=run.input_snapshot_hash,
            runtime_ms=run.runtime_ms or 0,
            metrics=run.metrics,
            assignments=[
                OptimizationAssignmentView(
                    employee_id=assignment.employee_id,
                    demand_id=assignment.role_demand_id,
                    starts_at=assignment.starts_at,
                    ends_at=assignment.ends_at,
                    incremental_cost_cents=assignment.incremental_cost_cents,
                )
                for assignment in assignments
            ],
            training=[
                OptimizationTrainingView(
                    employee_id=action.employee_id,
                    training_catalog_id=action.training_catalog_id,
                    ready_at=action.ready_at,
                    cost_cents=action.cost_cents,
                    duration_minutes=action.duration_minutes,
                )
                for action in training
            ],
            blockers=[OptimizationBlockerView.model_validate(blocker) for blocker in blockers],
            created_by=run.created_by,
            created_at=run.created_at,
        )
