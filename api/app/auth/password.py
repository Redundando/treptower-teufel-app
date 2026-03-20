from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    # bcrypt returns bytes, store as utf-8 string for portability.
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        # If the stored hash is malformed, fail closed.
        return False

