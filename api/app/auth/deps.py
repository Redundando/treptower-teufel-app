from __future__ import annotations

import uuid
from typing import TypedDict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.connection import connect

from .tokens import decode_access_token


class AuthenticatedUser(TypedDict):
    id: str
    email: str
    role: str
    is_active: bool


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload.get("sub")))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    conn = await connect()
    try:
        row = await conn.fetchrow(
            "SELECT id, email, role, is_active FROM app_users WHERE id = $1",
            user_id,
        )
        if row is None or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")

        return {
            "id": str(row["id"]),
            "email": row["email"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
        }
    finally:
        await conn.close()


def require_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user

