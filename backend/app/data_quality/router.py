from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data_quality.schemas import DataQualityOverview
from app.data_quality.service import DataQualityService
from app.workforce.router import request_session

router = APIRouter(prefix="/data-quality", tags=["data quality"])


@router.get("/overview", response_model=DataQualityOverview)
def data_quality_overview(
    session: Annotated[Session, Depends(request_session)],
) -> DataQualityOverview:
    return DataQualityService(session).overview()
