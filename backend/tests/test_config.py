from app.core.config import Settings


def test_settings_exclude_llm_and_oauth_configuration() -> None:
    """Catch reintroduction of removed model-runtime or OAuth configuration."""
    settings = Settings(_env_file=None)

    assert settings.app_name == "Tequaly Workforce Readiness"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert {
        "llm_enabled",
        "llm_api_key",
        "llm_base_url",
        "llm_model",
        "llm_timeout_seconds",
        "public_base_url",
        "mcp_remote_enabled",
        "mcp_access_token_minutes",
        "mcp_refresh_token_days",
        "mcp_oauth_secret",
        "mcp_allowed_redirect_hosts",
        "mcp_tool_timeout_seconds",
        "mcp_max_request_bytes",
        "mcp_rate_limit_per_minute",
    }.isdisjoint(Settings.model_fields)
