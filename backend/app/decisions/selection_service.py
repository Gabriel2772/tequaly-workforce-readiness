from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decisions.models import AuditEvent, DecisionRun, DecisionSelection
from app.decisions.schemas import SelectedDecision
from app.training.operation_service import TrainingPlanningService


class DecisionRunNotFoundError(LookupError):
    pass


class DecisionRunNotSelectableError(RuntimeError):
    pass


class DecisionSelectionService:
    def __init__(self, session: Session, actor_id: str) -> None:
        self._session = session
        self._actor_id = actor_id

    def select_scenario(
        self,
        decision_run_id: UUID,
        note: str | None,
    ) -> SelectedDecision:
        run = self._session.get(DecisionRun, decision_run_id)
        if run is None:
            raise DecisionRunNotFoundError(str(decision_run_id))
        if run.status not in {"OPTIMAL", "FEASIBLE", "TIMEOUT_FEASIBLE"}:
            raise DecisionRunNotSelectableError(run.status)
        normalized_note = note.strip() if note and note.strip() else None
        active = self._session.scalar(
            select(DecisionSelection)
            .where(
                DecisionSelection.operation_id == run.operation_id,
                DecisionSelection.superseded_at.is_(None),
            )
            .order_by(DecisionSelection.selected_at.desc(), DecisionSelection.id.desc())
            .limit(1)
        )
        if (
            active is not None
            and active.decision_run_id == decision_run_id
            and active.note == normalized_note
        ):
            previous = self._session.scalar(
                select(DecisionSelection).where(
                    DecisionSelection.superseded_by_selection_id == active.id
                )
            )
            return self._view(
                active,
                supersedes=(previous.decision_run_id if previous else None),
                idempotent=True,
            )

        if run.metrics.get("eligibility_run_id") is not None:
            TrainingPlanningService(self._session).materialize_for_decision(decision_run_id)

        occurred_at = datetime.now(UTC)
        superseded_run_id = active.decision_run_id if active is not None else None
        selection = DecisionSelection(
            decision_run_id=decision_run_id,
            operation_id=run.operation_id,
            actor_id=self._actor_id,
            note=normalized_note,
            selected_at=occurred_at,
        )
        self._session.add(selection)
        self._session.flush()
        if active is not None:
            active.superseded_at = occurred_at
            active.superseded_by_selection_id = selection.id
            self._session.add(
                AuditEvent(
                    actor_id=self._actor_id,
                    event_type="decision.selection_superseded",
                    aggregate_type="decision_run",
                    aggregate_id=decision_run_id,
                    payload={
                        "superseded_decision_run_id": str(active.decision_run_id),
                        "replacement_decision_run_id": str(decision_run_id),
                    },
                    occurred_at=occurred_at,
                )
            )
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type="decision.scenario_selected",
                aggregate_type="decision_run",
                aggregate_id=decision_run_id,
                payload={
                    "operation_id": str(run.operation_id),
                    "selection_id": str(selection.id),
                    "note": normalized_note,
                    "supersedes_decision_run_id": (
                        str(superseded_run_id) if superseded_run_id else None
                    ),
                },
                occurred_at=occurred_at + timedelta(microseconds=1),
            )
        )
        self._session.flush()
        return self._view(selection, supersedes=superseded_run_id, idempotent=False)

    def _view(
        self,
        selection: DecisionSelection,
        *,
        supersedes: UUID | None,
        idempotent: bool,
    ) -> SelectedDecision:
        return SelectedDecision(
            id=selection.id,
            decision_run_id=selection.decision_run_id,
            operation_id=selection.operation_id,
            actor_id=selection.actor_id,
            note=selection.note,
            selected_at=selection.selected_at,
            supersedes_decision_run_id=supersedes,
            idempotent=idempotent,
        )
