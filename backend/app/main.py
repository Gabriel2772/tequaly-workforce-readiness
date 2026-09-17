from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth.router import router as auth_router
from app.calibration.router import router as calibration_router
from app.core.config import Settings
from app.dashboard.router import router as dashboard_router
from app.data_quality.router import router as data_quality_router
from app.db.session import create_session_factory
from app.decisions.router import router as decisions_router
from app.eligibility.router import router as eligibility_router
from app.exports.router import router as exports_router
from app.fragility.router import router as fragility_router
from app.imports.router import router as imports_router
from app.mcp_connections.router import router as mcp_connections_router
from app.operations.router import router as operations_router
from app.optimization.router import router as optimization_router
from app.training.router import investment_router
from app.training.router import router as training_router
from app.workforce.router import reference_router
from app.workforce.router import router as workforce_router


def create_app(
    *,
    session_factory: sessionmaker[Session] | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Create the HTTP adapter with its dependency-free health contract."""
    owned_engine: Engine | None = None
    if session_factory is None:
        owned_engine, session_factory = create_session_factory()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        if owned_engine is not None:
            owned_engine.dispose()

    app = FastAPI(title="Tequaly Workforce Readiness", lifespan=lifespan)
    app.state.session_factory = session_factory
    settings = settings or Settings()
    if (
        settings.auth_required
        and settings.environment != "development"
        and settings.session_secret == "development-only-change-before-production"
    ):
        raise RuntimeError("TWR_SESSION_SECRET must be configured when authentication is required")
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin.rstrip("/")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-TWR-Actor", "X-TWR-Role"],
    )
    app.include_router(auth_router)
    app.include_router(workforce_router)
    app.include_router(calibration_router)
    app.include_router(dashboard_router)
    app.include_router(data_quality_router)
    app.include_router(decisions_router)
    app.include_router(reference_router)
    app.include_router(operations_router)
    app.include_router(eligibility_router)
    app.include_router(exports_router)
    app.include_router(fragility_router)
    app.include_router(imports_router)
    app.include_router(mcp_connections_router)
    app.include_router(optimization_router)
    app.include_router(training_router)
    app.include_router(investment_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
