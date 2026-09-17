from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def create_session_factory(
    settings: Settings | None = None,
) -> tuple[Engine, sessionmaker[Session]]:
    resolved_settings = settings or Settings()
    engine = create_engine(resolved_settings.database_url, pool_pre_ping=True)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def get_session(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
