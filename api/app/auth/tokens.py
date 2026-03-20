from __future__ import annotations

import time
import uuid

from app.config import CONFIG


def _require_jwt_secret() -> str:
    secret = (CONFIG["app"]["jwt"]["secret_key"] or "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not set")
    return secret


def create_access_token(*, user_id: uuid.UUID, email: str, role: str) -> str:
    """
    Create a signed access token for the API.

    Payload includes:
    - sub: user id
    - email, role for convenience (role is still enforced by DB check).
    """
    now = int(time.time())
    access_token_seconds = int(CONFIG["app"]["jwt"]["access_token_seconds"])
    exp = now + access_token_seconds

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": exp,
    }
    from jose import jwt  # local import keeps module import light

    algorithm = str(CONFIG["app"]["jwt"]["algorithm"])
    return jwt.encode(payload, _require_jwt_secret(), algorithm=algorithm)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate token signature + expiry.

    Raises RuntimeError/ValueError on invalid tokens.
    """
    from jose import jwt  # local import keeps module import light
    secret = _require_jwt_secret()
    algorithm = str(CONFIG["app"]["jwt"]["algorithm"])
    return jwt.decode(token, secret, algorithms=[algorithm])

