from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_write_actor
from app.decisions.models import AuditEvent, DecisionRun, DecisionSelection
from app.decisions.outcome_service import (
    DecisionOutcomeService,
    OutcomeAlreadyRecordedError,
    OutcomeDecisionRunNotFoundError,
    OutcomeReferenceError,
    OutcomeSelectionRequiredError,
    OutcomeSnapshotError,
    get_outcome_context,
    get_outcome_view,
)
from app.decisions.repository import DecisionRepository
from app.decisions.schemas import (
    DecisionOutcomeView,
    DecisionRunDetail,
    DecisionTimelineEvent,
    RecordOutcomeCommand,
    SelectedDecision,
    SelectScenarioCommand,
)
from app.decisions.selection_service import (
    DecisionRunNotFoundError,
    DecisionRunNotSelectableError,
    DecisionSelectionService,
)
from app.optimization.schemas import ScenarioCollection
from app.workforce.router import request_session

router = APIRouter(prefix="/decision-runs", tags=["decisions"])


@router.post(
    "/{decision_run_id}/outcome",
    response_model=DecisionOutcomeView,
    status_code=status.HTTP_201_CREATED,
)
def record_outcome(
    decision_run_id: UUID,
    command: RecordOutcomeCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> DecisionOutcomeView:
    try:
        result = DecisionOutcomeService(session, actor_id).record_outcome(
            decision_run_id, command
        )
        session.commit()
        return result
    except OutcomeDecisionRunNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "decision_run_not_found", "message": "Decision run not found"},
        ) from error
    except OutcomeSelectionRequiredError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "selection_required", "message": "Select the scenario first"},
        ) from error
    except OutcomeAlreadyRecordedError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "outcome_already_recorded", "message": "Outcome already recorded"},
        ) from error
    except OutcomeReferenceError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_outcome_reference", "message": str(error)},
        ) from error
    except OutcomeSnapshotError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "outcome_snapshot_incomplete",
                "message": "Decision snapshot is incomplete",
            },
        ) from error


@router.post("/{decision_run_id}/select", response_model=SelectedDecision)
def select_scenario(
    decision_run_id: UUID,
    command: SelectScenarioCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> SelectedDecision:
    try:
        result = DecisionSelectionService(session, actor_id).select_scenario(
            decision_run_id, command.note
        )
        session.commit()
        return result
    except DecisionRunNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "decision_run_not_found", "message": "Decision run not found"},
        ) from error
    except DecisionRunNotSelectableError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "decision_run_not_selectable",
                "message": "Only feasible scenarios can be selected",
            },
        ) from error


@router.get("", response_model=ScenarioCollection)
def list_decision_runs(
    session: Annotated[Session, Depends(request_session)],
) -> ScenarioCollection:
    return DecisionRepository(session).list_all()


@router.get("/{decision_run_id}", response_model=DecisionRunDetail)
def get_decision_run(
    decision_run_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> DecisionRunDetail:
    run = session.get(DecisionRun, decision_run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "decision_run_not_found", "message": "Decision run not found"},
        )
    run_view = DecisionRepository(session).to_view(run)
    selection = session.scalar(
        select(DecisionSelection)
        .where(DecisionSelection.decision_run_id == decision_run_id)
        .order_by(DecisionSelection.selected_at.desc(), DecisionSelection.id.desc())
        .limit(1)
    )
    selected_view: SelectedDecision | None = None
    if selection is not None:
        previous = session.scalar(
            select(DecisionSelection).where(
                DecisionSelection.superseded_by_selection_id == selection.id
            )
        )
        selected_view = SelectedDecision(
            id=selection.id,
            decision_run_id=selection.decision_run_id,
            operation_id=selection.operation_id,
            actor_id=selection.actor_id,
            note=selection.note,
            selected_at=selection.selected_at,
            supersedes_decision_run_id=(previous.decision_run_id if previous else None),
        )
    events = [
        DecisionTimelineEvent(
            event_type="decision.run_completed",
            occurred_at=run.created_at,
            actor_id=run.created_by,
            payload={
                "objective": run.objective,
                "status": run.status,
                "input_snapshot_hash": run.input_snapshot_hash,
            },
        )
    ]
    events.extend(
        DecisionTimelineEvent(
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            actor_id=event.actor_id,
            payload=event.payload,
        )
        for event in session.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.aggregate_type == "decision_run",
                AuditEvent.aggregate_id == decision_run_id,
            )
            .order_by(AuditEvent.occurred_at, AuditEvent.id)
        )
    )
    return DecisionRunDetail(
        run=run_view,
        selection=selected_view,
        timeline=events,
        outcome=get_outcome_view(session, decision_run_id),
        outcome_context=get_outcome_context(session, decision_run_id),
    )
