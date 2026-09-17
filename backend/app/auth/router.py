from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import AuthenticatedActor, require_session_actor
from app.auth.models import AppUser
from app.auth.schemas import LoginCommand, SessionView, UserRole
from app.auth.security import create_session_token, hash_password, verify_password
from app.core.config import Settings
from app.workforce.router import request_session

router = APIRouter(prefix="/auth", tags=["auth"])
_DUMMY_PASSWORD_HASH = hash_password("timing-comparison-only")


@router.post("/login", response_model=SessionView)
def login(
    command: LoginCommand,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(request_session)],
) -> SessionView:
    username = command.username.strip().casefold()
    user = session.scalar(select(AppUser).where(func.lower(AppUser.username) == username))
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    if user is None or not verify_password(command.password, password_hash) or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Usuário ou senha inválidos."},
        )
    if user.role not in {"viewer", "planner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "invalid_role", "message": "Perfil de acesso inválido."},
        )
    role = cast(UserRole, user.role)
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=settings.session_hours)
    token = create_session_token(
        user_id=str(user.id),
        username=user.username,
        role=role,
        secret=settings.session_secret,
        expires_at=expires_at,
    )
    user.last_login_at = now
    session.commit()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_hours * 3600,
        expires=expires_at,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return SessionView(
        id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        role=role,
        expires_at=expires_at,
    )


@router.get("/me", response_model=SessionView)
def me(actor: Annotated[AuthenticatedActor, Depends(require_session_actor)]) -> SessionView:
    assert actor.expires_at is not None
    return SessionView(
        id=actor.user_id,
        username=actor.username,
        display_name=actor.display_name,
        role=actor.role,
        expires_at=actor.expires_at,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> None:
    settings: Settings = request.app.state.settings
    response.delete_cookie(settings.session_cookie_name, path="/")
