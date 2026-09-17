from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_write_actor
from app.calibration.service import (
    CalibrationConfirmationRequiredError,
    CalibrationService,
    CalibrationSuggestionAlreadyAppliedError,
    CalibrationSuggestionNotFoundError,
    InsufficientCalibrationSamplesError,
)
from app.calibration.types import (
    ApplyCalibrationSuggestionCommand,
    CalibrationParameterView,
    CalibrationSuggestionView,
    CreateCalibrationSuggestionCommand,
)
from app.workforce.router import request_session

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.post(
    "/suggestions",
    response_model=CalibrationSuggestionView,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion(
    command: CreateCalibrationSuggestionCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CalibrationSuggestionView:
    try:
        result = CalibrationService(session, actor_id).suggest(
            command.parameter, command.category
        )
        session.commit()
        return result
    except InsufficientCalibrationSamplesError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "insufficient_calibration_samples",
                "message": "At least five observations are required",
                "sample_size": error.sample_size,
                "minimum_sample_size": error.minimum_sample_size,
            },
        ) from error


@router.post(
    "/suggestions/{suggestion_id}/apply",
    response_model=CalibrationParameterView,
)
def apply_suggestion(
    suggestion_id: UUID,
    command: ApplyCalibrationSuggestionCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_write_actor)],
) -> CalibrationParameterView:
    try:
        result = CalibrationService(session, actor_id).apply_suggestion(
            suggestion_id, confirmed=command.confirmed
        )
        session.commit()
        return result
    except CalibrationSuggestionNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "suggestion_not_found", "message": "Suggestion not found"},
        ) from error
    except CalibrationConfirmationRequiredError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "confirmation_required",
                "message": "Explicit confirmation is required",
            },
        ) from error
    except CalibrationSuggestionAlreadyAppliedError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "suggestion_already_applied",
                "message": "Suggestion has already been applied",
            },
        ) from error
