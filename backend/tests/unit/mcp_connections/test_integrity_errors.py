import sqlite3
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.mcp_connections.router import _is_duplicate_name_error


class _PostgresIntegrityError(Exception):
    def __init__(self, constraint_name: str) -> None:
        super().__init__(f'duplicate key violates unique constraint "{constraint_name}"')
        self.diag = SimpleNamespace(constraint_name=constraint_name)


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        (_PostgresIntegrityError("uq_user_mcp_connection_name"), True),
        (_PostgresIntegrityError("uq_app_users_username"), False),
        (
            sqlite3.IntegrityError(
                "UNIQUE constraint failed: user_mcp_connections.user_id, "
                "user_mcp_connections.client_type, user_mcp_connections.name"
            ),
            True,
        ),
        (
            sqlite3.IntegrityError(
                "UNIQUE constraint failed: user_mcp_connections.endpoint_url"
            ),
            False,
        ),
        (sqlite3.IntegrityError("CHECK constraint failed: enabled_boolean"), False),
    ],
)
def test_duplicate_name_detection_is_limited_to_the_named_constraint(
    original: BaseException,
    expected: bool,
) -> None:
    error = IntegrityError("INSERT", {}, original)

    assert _is_duplicate_name_error(error) is expected
