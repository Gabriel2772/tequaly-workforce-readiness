from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.auth.models import AppUser
from app.auth.security import InvalidSessionToken, SessionTokenClaims, parse_session_token
from app.core.config import Settings

UserRole = Literal["viewer", "planner", "admin"]


@dataclass(frozen=True)
class AuthenticatedActor:
    user_id: str
    username: str
    display_name: str
    role: UserRole
    expires_at: datetime | None


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "authentication_required", "message": "Autentica��o necess�ria."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return request.cookies.get(settings.session_cookie_name)


def _claims(request: Request, settings: Settings) -> SessionTokenClaims | None:
    token = _token(request, settings)
    if not token:
        return None
    try:
        return parse_session_token(token, settings.session_secret)
    except InvalidSessionToken as error:
        raise _unauthorized() from error


def require_session_actor(request: Request) -> AuthenticatedActor:
    settings: Settings = request.app.state.settings
    claims = _claims(request, settings)
    if claims is None:
        raise _unauthorized()
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        try:
            user = session.get(AppUser, UUID(claims.user_id))
        except ValueError as error:
            raise _unauthorized() from error
        if (
            user is None
            or not user.active
            or user.username != claims.username
            or user.role != claims.role
        ):
            raise _unauthorized()
        return AuthenticatedActor(
            user_id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            role=user.role,  # type: ignore[arg-type]
            expires_at=claims.expires_at,
        )


def _require_roles(
    request: Request,
    allowed: set[UserRole],
    *,
    demo_default_role: UserRole,
    forbidden_code: str,
    forbidden_message: str,
) -> str:
    settings: Settings = request.app.state.settings
    claims = _claims(request, settings)
    if claims is not None:
        actor = require_session_actor(request)
        if actor.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": forbidden_code, "message": forbidden_message},
            )
        return actor.username
    if settings.auth_required:
        raise _unauthorized()
    role = request.headers.get("X-TWR-Role", demo_default_role).strip().lower()
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": forbidden_code, "message": forbidden_message},
        )
    return request.headers.get("X-TWR-Actor", "local-demo-user").strip() or "local-demo-user"


def require_read_actor(request: Request) -> str:
    return _require_roles(
        request,
        {"viewer", "planner", "admin"},
        demo_default_role="viewer",
        forbidden_code="read_forbidden",
        forbidden_message="O perfil atual n�o pode consultar estes dados.",
    )


def require_write_actor(request: Request) -> str:
    return _require_roles(
        request,
        {"planner", "admin"},
        demo_default_role="planner",
        forbidden_code="write_forbidden",
        forbidden_message="O perfil atual n�o pode modificar dados operacionais.",
    )


def require_admin_actor(request: Request) -> str:
    return _require_roles(
        request,
        {"admin"},
        demo_default_role="viewer",
        forbidden_code="admin_forbidden",
        forbidden_message="Esta a��o exige perfil administrador.",
    )
