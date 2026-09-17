from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_read_actor
from app.exports.service import ExportService, validate_export_type
from app.workforce.router import request_session

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{export_type}")
def export_data(
    export_type: str,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_read_actor)],
    format: Literal["csv", "xlsx"] = "csv",
    operation_id: UUID | None = None,
    active: bool | None = None,
) -> Response:
    try:
        result = ExportService(session, actor_id).export(
            validate_export_type(export_type),
            format,
            operation_id=operation_id,
            active=active,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": str(error), "message": "Exportação inválida."},
        ) from error
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )
