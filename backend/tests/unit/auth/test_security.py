from datetime import UTC, datetime, timedelta

import pytest

from app.auth.security import (
    InvalidSessionToken,
    create_session_token,
    hash_password,
    parse_session_token,
    verify_password,
)


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("TequalyDemo!2026")
    second = hash_password("TequalyDemo!2026")

    assert first != second
    assert "TequalyDemo!2026" not in first
    assert verify_password("TequalyDemo!2026", first) is True
    assert verify_password("senha-incorreta", first) is False


def test_signed_session_rejects_tampering_and_expiration() -> None:
    now = datetime(2026, 8, 24, 12, tzinfo=UTC)
    token = create_session_token(
        user_id="user-1",
        username="planejador.demo",
        role="planner",
        secret="test-secret-with-enough-entropy",
        expires_at=now + timedelta(hours=8),
    )

    claims = parse_session_token(token, "test-secret-with-enough-entropy", now=now)
    assert claims.user_id == "user-1"
    assert claims.role == "planner"

    with pytest.raises(InvalidSessionToken):
        parse_session_token(f"{token[:-1]}x", "test-secret-with-enough-entropy", now=now)
    with pytest.raises(InvalidSessionToken):
        parse_session_token(token, "test-secret-with-enough-entropy", now=now + timedelta(days=1))
