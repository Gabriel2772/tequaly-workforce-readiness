from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin_actor
from app.imports.commit_service import ImportCommitError, ImportCommitService
from app.imports.preview_service import ImportPreviewError, ImportPreviewService
from app.imports.types import (
    ImportCommitCommand,
    ImportCommitSummary,
    ImportPreviewCommand,
    ImportPreviewView,
)
from app.workforce.router import request_session

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/preview", response_model=ImportPreviewView, status_code=status.HTTP_201_CREATED)
def preview_import(
    command: ImportPreviewCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_admin_actor)],
) -> ImportPreviewView:
    try:
        result = ImportPreviewService(session, actor_id).preview(command)
        session.commit()
        return result
    except ImportPreviewError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_import", "message": str(error)},
        ) from error


@router.post("/commit", response_model=ImportCommitSummary)
def commit_import(
    command: ImportCommitCommand,
    session: Annotated[Session, Depends(request_session)],
    actor_id: Annotated[str, Depends(require_admin_actor)],
) -> ImportCommitSummary:
    try:
        result = ImportCommitService(session, actor_id).commit(
            command.preview_token, confirmed=command.confirmed
        )
        session.commit()
        return result
    except ImportCommitError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": str(error), "message": "A importação não pode ser confirmada."},
        ) from error
