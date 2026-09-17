from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.fragility.service import FragilityService
from app.fragility.types import FragilityReport
from app.workforce.router import request_session

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/fragility", response_model=FragilityReport)
def get_fragility(
    session: Annotated[Session, Depends(request_session)],
    horizon_days: Annotated[int, Query(ge=1, le=3_650)] = 180,
    operation_ids: Annotated[list[UUID] | None, Query()] = None,
) -> FragilityReport:
    return FragilityService(session).calculate(horizon_days, operation_ids)
