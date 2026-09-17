from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.training.investment_service import InvestmentPlanningService
from app.training.operation_service import (
    EligibilityRunRequiredForTrainingError,
    TrainingDecisionRunNotFoundError,
    TrainingOperationNotFoundError,
    TrainingPlanningService,
)
from app.training.types import InvestmentPlan, InvestmentPlanRequest, OperationTrainingPlan
from app.workforce.router import request_session

router = APIRouter(prefix="/operations", tags=["training"])
investment_router = APIRouter(prefix="/training", tags=["training"])


@investment_router.post("/investment-plan", response_model=InvestmentPlan)
def create_investment_plan(
    command: InvestmentPlanRequest,
    session: Annotated[Session, Depends(request_session)],
) -> InvestmentPlan:
    return InvestmentPlanningService(session).plan_investment(
        command.horizon,
        command.budget_cents,
        command.weights,
    )


@router.get("/{operation_id}/training-plan", response_model=OperationTrainingPlan)
def get_operation_training_plan(
    operation_id: UUID,
    session: Annotated[Session, Depends(request_session)],
    decision_run_id: UUID | None = None,
) -> OperationTrainingPlan:
    try:
        return TrainingPlanningService(session).for_operation(operation_id, decision_run_id)
    except TrainingOperationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "operation_not_found", "message": "Operation not found"},
        ) from error
    except TrainingDecisionRunNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "decision_run_not_found",
                "message": "Decision run does not belong to this operation",
            },
        ) from error
    except EligibilityRunRequiredForTrainingError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "eligibility_run_required",
                "message": "Run eligibility before planning training",
            },
        ) from error
