from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime


class InvalidSessionToken(ValueError):
    pass


@dataclass(frozen=True)
class SessionTokenClaims:
    user_id: str
    username: str
    role: str
    expires_at: datetime


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=actual_salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${_encode(actual_salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=_decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_decode(expected)),
        )
        return hmac.compare_digest(actual, _decode(expected))
    except (ValueError, TypeError):
        return False


def create_session_token(
    *,
    user_id: str,
    username: str,
    role: str,
    secret: str,
    expires_at: datetime,
) -> str:
    payload = {
        "sub": user_id,
        "usr": username,
        "rol": role,
        "exp": int(expires_at.timestamp()),
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _encode(
        hmac.new(secret.encode(), encoded_payload.encode(), hashlib.sha256).digest()
    )
    return f"{encoded_payload}.{signature}"


def parse_session_token(
    token: str, secret: str, *, now: datetime | None = None
) -> SessionTokenClaims:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        if _encode(_decode(encoded_signature)) != encoded_signature:
            raise InvalidSessionToken("non_canonical_signature")
        expected_signature = hmac.new(
            secret.encode(), encoded_payload.encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected_signature, _decode(encoded_signature)):
            raise InvalidSessionToken("invalid_signature")
        payload = json.loads(_decode(encoded_payload))
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
        current_time = now or datetime.now(UTC)
        if expires_at <= current_time:
            raise InvalidSessionToken("expired_token")
        role = str(payload["rol"])
        if role not in {"viewer", "planner", "admin"}:
            raise InvalidSessionToken("invalid_role")
        return SessionTokenClaims(
            user_id=str(payload["sub"]),
            username=str(payload["usr"]),
            role=role,
            expires_at=expires_at,
        )
    except InvalidSessionToken:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise InvalidSessionToken("malformed_token") from error
