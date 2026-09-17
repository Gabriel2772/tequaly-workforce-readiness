from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_write_actor
from app.decisions.repository import DecisionRepository
from app.operations.models import Operation
from app.optimization.schemas import (
    OptimizationResultView,
    OptimizeCommand,
    ScenarioCollection,
)
from app.optimization.service import (
    EligibilityRunRequiredError,
    OperationOptimizationNotFoundError,
    OptimizationService,
)
from app.workforce.router import request_session

router = APIRouter(prefix="/operations", tags=["optimization"])


@router.post(
    "/{operation_id}/optimize",
    response_model=OptimizationResultView,
    status_code=status.HTTP_201_CREATED,
)
def optimize_operation(
    operation_id: UUID,
    command: OptimizeCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> OptimizationResultView:
    try:
        result = OptimizationService(session, actor_id).optimize(operation_id, command.objective)
        session.commit()
        return result
    except OperationOptimizationNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        ) from error
    except EligibilityRunRequiredError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "eligibility_run_required",
                "message": "Run eligibility before optimization",
            },
        ) from error


@router.get("/{operation_id}/scenarios", response_model=ScenarioCollection)
def list_scenarios(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> ScenarioCollection:
    if session.get(Operation, operation_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        )
    return DecisionRepository(session).list_scenarios(operation_id)
