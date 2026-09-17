from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side configuration loaded from ``TWR_*`` environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TWR_",
        extra="ignore",
    )

    app_name: str = "Tequaly Workforce Readiness"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://twr:twr@localhost:5432/twr"
    frontend_origin: str = "http://localhost:3000"
    auth_required: bool = False
    session_secret: str = "development-only-change-before-production"
    session_cookie_name: str = "twr_session"
    session_hours: int = 8
    secure_cookies: bool = False
