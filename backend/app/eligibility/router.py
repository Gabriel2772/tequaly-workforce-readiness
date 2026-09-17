from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_write_actor
from app.eligibility.candidate_pool import EligibilityOperationNotFoundError
from app.eligibility.run_service import (
    EligibilityRunNotFoundError,
    EligibilityRunQueryService,
    EligibilityRunService,
)
from app.eligibility.schemas import EligibilityRunView
from app.workforce.router import request_session

router = APIRouter(prefix="/operations", tags=["eligibility"])


@router.get(
    "/{operation_id}/eligibility/latest",
    response_model=EligibilityRunView,
)
def get_latest_operation_eligibility(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
) -> EligibilityRunView:
    try:
        return EligibilityRunQueryService(session).get_latest(operation_id)
    except EligibilityRunNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "eligibility_run_not_found",
                "message": "Run eligibility before viewing results",
            },
        ) from error


@router.post(
    "/{operation_id}/eligibility/run",
    response_model=EligibilityRunView,
    status_code=status.HTTP_201_CREATED,
)
def run_operation_eligibility(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> EligibilityRunView:
    try:
        result = EligibilityRunService(session, actor_id).run_operation(operation_id)
        session.commit()
        return result
    except EligibilityOperationNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        ) from error
