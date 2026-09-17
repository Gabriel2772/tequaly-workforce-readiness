from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import AuthenticatedActor, require_session_actor
from app.mcp.tools.read_tools import build_read_registry
from app.mcp_connections.schemas import (
    McpConnectionCreate,
    McpConnectionUpdate,
    McpConnectionValidation,
    McpConnectionView,
    McpToolView,
)
from app.mcp_connections.service import (
    InvalidMcpEndpoint,
    McpConnectionNotFoundError,
    McpConnectionService,
)
from app.workforce.router import request_session

router = APIRouter(prefix="/mcp-connections", tags=["mcp-connections"])

_DUPLICATE_NAME_CONSTRAINT = "uq_user_mcp_connection_name"
_SQLITE_DUPLICATE_NAME_MESSAGE = (
    "unique constraint failed: user_mcp_connections.user_id, "
    "user_mcp_connections.client_type, user_mcp_connections.name"
)


def _is_duplicate_name_error(error: IntegrityError) -> bool:
    diagnostic = getattr(error.orig, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return str(constraint_name) == _DUPLICATE_NAME_CONSTRAINT
    return str(error.orig).casefold() == _SQLITE_DUPLICATE_NAME_MESSAGE


def _duplicate_name_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "duplicate_mcp_connection",
            "message": "Já existe uma conexão com esse nome para o destino.",
        },
    )


def _service(
    request: Request,
    session: Session,
    actor: AuthenticatedActor,
) -> McpConnectionService:
    return McpConnectionService(
        session,
        user_id=UUID(actor.user_id),
        actor_id=actor.user_id,
        environment=request.app.state.settings.environment,
    )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "mcp_connection_not_found",
            "message": "Conexão MCP não encontrada.",
        },
    )


def _invalid_endpoint(error: InvalidMcpEndpoint) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_mcp_endpoint", "message": str(error)},
    )


@router.get("", response_model=list[McpConnectionView])
def list_connections(
    request: Request,
    session: Annotated[Session, Depends(request_session)],
    actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> list[McpConnectionView]:
    records = _service(request, session, actor).list_for_user()
    return [McpConnectionView.model_validate(record) for record in records]


@router.post("", response_model=McpConnectionView, status_code=status.HTTP_201_CREATED)
def create_connection(
    command: McpConnectionCreate,
    request: Request,
    session: Annotated[Session, Depends(request_session)],
    actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> McpConnectionView:
    try:
        connection = _service(request, session, actor).create(command)
        session.commit()
    except InvalidMcpEndpoint as error:
        session.rollback()
        raise _invalid_endpoint(error) from error
    except IntegrityError as error:
        session.rollback()
        if not _is_duplicate_name_error(error):
            raise
        raise _duplicate_name_conflict() from error
    return McpConnectionView.model_validate(connection)


@router.get("/catalog", response_model=list[McpToolView])
def catalog(
    _actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> list[McpToolView]:
    return [McpToolView.model_validate(item) for item in build_read_registry().catalog()]


@router.patch("/{connection_id}", response_model=McpConnectionView)
def update_connection(
    connection_id: UUID,
    command: McpConnectionUpdate,
    request: Request,
    session: Annotated[Session, Depends(request_session)],
    actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> McpConnectionView:
    try:
        connection = _service(request, session, actor).update(connection_id, command)
        session.commit()
    except McpConnectionNotFoundError as error:
        session.rollback()
        raise _not_found() from error
    except InvalidMcpEndpoint as error:
        session.rollback()
        raise _invalid_endpoint(error) from error
    except IntegrityError as error:
        session.rollback()
        if not _is_duplicate_name_error(error):
            raise
        raise _duplicate_name_conflict() from error
    return McpConnectionView.model_validate(connection)


@router.post("/{connection_id}/validate", response_model=McpConnectionValidation)
def validate_connection(
    connection_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(request_session)],
    actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> McpConnectionValidation:
    try:
        result = _service(request, session, actor).validate(connection_id)
        session.commit()
    except McpConnectionNotFoundError as error:
        session.rollback()
        raise _not_found() from error
    except InvalidMcpEndpoint as error:
        session.rollback()
        raise _invalid_endpoint(error) from error
    return result


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: UUID,
    request: Request,
    session: Annotated[Session, Depends(request_session)],
    actor: Annotated[AuthenticatedActor, Depends(require_session_actor)],
) -> Response:
    try:
        _service(request, session, actor).delete(connection_id)
        session.commit()
    except McpConnectionNotFoundError as error:
        session.rollback()
        raise _not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
