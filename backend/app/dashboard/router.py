from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dashboard.schemas import DashboardOverview
from app.dashboard.service import DashboardService
from app.workforce.router import request_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    session: Annotated[Session, Depends(request_session)],
    horizon_days: Annotated[int, Query(ge=1, le=730)] = 180,
) -> DashboardOverview:
    return DashboardService(session).get_overview(horizon_days)
