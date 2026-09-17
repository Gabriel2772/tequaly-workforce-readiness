import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Column, ForeignKey, MetaData, String, Table, create_engine, inspect, text
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).parents[2]
LEGACY_OAUTH_TABLES = {
    "mcp_oauth_clients",
    "mcp_authorization_requests",
    "mcp_authorization_codes",
    "mcp_authorization_grants",
    "mcp_refresh_tokens",
}


def _config() -> Config:
    return Config(BACKEND_ROOT / "alembic.ini")


def _mark_database_as_legacy_oauth(database_url: str) -> None:
    metadata = MetaData()
    Table("mcp_oauth_clients", metadata, Column("id", String, primary_key=True))
    Table("mcp_authorization_requests", metadata, Column("id", String, primary_key=True))
    grants = Table("mcp_authorization_grants", metadata, Column("id", String, primary_key=True))
    Table(
        "mcp_authorization_codes",
        metadata,
        Column("id", String, primary_key=True),
        Column("grant_id", ForeignKey(grants.c.id), nullable=False),
    )
    Table(
        "mcp_refresh_tokens",
        metadata,
        Column("id", String, primary_key=True),
        Column("grant_id", ForeignKey(grants.c.id), nullable=False),
    )

    engine = create_engine(database_url)
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE alembic_version SET version_num = '0010_mcp_oauth'")
            )
    finally:
        engine.dispose()


def test_database_has_a_single_linear_migration_head() -> None:
    scripts = ScriptDirectory.from_config(_config())

    assert scripts.get_bases() == ["0001_core_schema"]
    assert len(scripts.get_heads()) == 1


def test_initial_migration_compiles_to_postgresql_sql(capsys: pytest.CaptureFixture[str]) -> None:
    config = _config()
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://unused:unused@localhost/unused")

    command.upgrade(config, "head", sql=True)

    ddl = capsys.readouterr().out.casefold()
    assert "create table app_users" in ddl
    assert "create table employees" in ddl
    assert "create table operations" in ddl
    assert "create table decision_runs" in ddl
    assert "create table calibration_suggestions" in ddl
    assert "create table user_mcp_connections" in ddl
    assert "create table evidence" not in ddl


def test_initial_migration_executes_a_fast_sqlite_round_trip(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migration-smoke.db').as_posix()}"
    config = _config()
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    assert {
        "employees",
        "operations",
        "decision_runs",
        "calibration_suggestions",
        "user_mcp_connections",
    } <= tables
    columns = {column["name"] for column in inspect(engine).get_columns("user_mcp_connections")}
    assert columns == {
        "id",
        "user_id",
        "name",
        "client_type",
        "endpoint_url",
        "transport",
        "notes",
        "enabled",
        "last_validated_at",
        "created_at",
        "updated_at",
    }
    assert not LEGACY_OAUTH_TABLES.intersection(tables)
    command.check(config)

    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()


def test_upgrade_from_legacy_oauth_revision_replaces_oauth_tables_with_registry(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'legacy-oauth.db').as_posix()}"
    config = _config()
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "0009_import_batches")
    _mark_database_as_legacy_oauth(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert "user_mcp_connections" in tables
        assert not LEGACY_OAUTH_TABLES.intersection(tables)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0010_user_mcp_connections"
            )
    finally:
        engine.dispose()


@pytest.mark.skipif(
    not os.getenv("TWR_TEST_DATABASE_URL"),
    reason="TWR_TEST_DATABASE_URL is required for the PostgreSQL round-trip",
)
def test_postgresql_upgrade_downgrade_upgrade_round_trip() -> None:
    database_url = os.environ["TWR_TEST_DATABASE_URL"]
    parsed_url = make_url(database_url)
    assert parsed_url.get_backend_name() == "postgresql"
    assert parsed_url.database and parsed_url.database.endswith("_test")

    engine = create_engine(database_url)
    required_tables = {
        "employees",
        "operations",
        "decision_runs",
        "user_mcp_connections",
    }
    assert not required_tables.intersection(inspect(engine).get_table_names())

    config = _config()
    config.set_main_option("sqlalchemy.url", database_url)
    try:
        command.upgrade(config, "head")
        assert required_tables <= set(inspect(engine).get_table_names())

        command.downgrade(config, "base")
        assert not required_tables.intersection(inspect(engine).get_table_names())

        command.upgrade(config, "head")
        assert required_tables <= set(inspect(engine).get_table_names())
    finally:
        command.downgrade(config, "base")
        engine.dispose()
