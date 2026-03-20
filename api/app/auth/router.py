from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal

from app.config import CONFIG

from app.db.connection import connect

from .deps import AuthenticatedUser, get_current_user, require_admin
from .password import hash_password, verify_password
from .tokens import create_access_token


router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    role: Literal["member", "admin"]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(body: LoginRequest) -> LoginResponse:
    email_norm = (body.email or "").strip().lower()
    password = body.password or ""
    if not email_norm or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")

    conn = await connect()
    try:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, role, is_active FROM app_users WHERE email = $1",
            email_norm,
        )
        if row is None or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(
            user_id=row["id"],
            email=row["email"],
            role=row["role"],
        )

        token_type = str(CONFIG["app"]["jwt"]["token_type"])
        return {
            "access_token": access_token,
            "token_type": token_type,
            "user": {
                "id": str(row["id"]),
                "email": row["email"],
                "role": row["role"],
            },
        }
    finally:
        await conn.close()


@router.get("/auth/me", response_model=UserOut, tags=["auth"])
async def me(user: AuthenticatedUser = Depends(get_current_user)) -> UserOut:
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: Literal["member", "admin"] = "member"


@router.post("/auth/admin/users", response_model=UserOut, tags=["auth"])
async def admin_create_user(
    body: CreateUserRequest,
    _: AuthenticatedUser = Depends(require_admin),
) -> UserOut:
    email_norm = (body.email or "").strip().lower()
    password = body.password or ""
    role = body.role
    if not email_norm or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")

    conn = await connect()
    try:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO app_users (email, password_hash, role)
                VALUES ($1, $2, $3)
                RETURNING id, email, role
                """,
                email_norm,
                hash_password(password),
                role,
            )
        except asyncpg.exceptions.UniqueViolationError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        if row is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed")

        return {"id": str(row["id"]), "email": row["email"], "role": row["role"]}
    finally:
        await conn.close()

