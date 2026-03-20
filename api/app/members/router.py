from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.deps import AuthenticatedUser, require_admin
from app.db.connection import connect


router = APIRouter()


_TYPED_COLUMNS: list[str] = [
    "mitgliedsnummer",
    "vorname",
    "nachname",
    "geburtsdatum",
    "eintrittsdatum",
    "austrittsdatum",
    "mitgliedsart",
    "strasse",
    "plz",
    "ort",
    "telefon_privat",
    "telefon_arbeit",
    "email_privat",
    "nx_ssp_registration_code",
    "beitragsnamen",
    "info",
]


class MemberOut(BaseModel):
    id: str
    netxp_id: str

    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime
    inactive_since: datetime | None

    # Typed CSV fields (never `netxp_raw`)
    mitgliedsnummer: str | None = None
    vorname: str | None = None
    nachname: str | None = None
    geburtsdatum: date | None = None
    eintrittsdatum: date | None = None
    austrittsdatum: date | None = None
    mitgliedsart: str | None = None
    strasse: str | None = None
    plz: str | None = None
    ort: str | None = None
    telefon_privat: str | None = None
    telefon_arbeit: str | None = None
    email_privat: str | None = None
    nx_ssp_registration_code: str | None = None
    beitragsnamen: str | None = None
    info: str | None = None


class MembersListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MemberOut]


def _normalize_search(search: str | None) -> str | None:
    s = (search or "").strip()
    return s or None


@router.get("/members", response_model=MembersListResponse, tags=["admin", "netxp-members"])
async def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None),
    active_only: bool = Query(True),
    _: AuthenticatedUser = Depends(require_admin),
) -> MembersListResponse:
    search_norm = _normalize_search(search)
    offset = (page - 1) * page_size

    where_clauses: list[str] = []
    params_base: list[Any] = []
    param_idx = 1

    if search_norm is not None:
        pattern = f"%{search_norm}%"
        where_clauses.append(
            "("
            f"nachname ILIKE ${param_idx} OR "
            f"vorname ILIKE ${param_idx} OR "
            f"netxp_id ILIKE ${param_idx} OR "
            f"mitgliedsnummer ILIKE ${param_idx}"
            ")"
        )
        params_base.append(pattern)
        param_idx += 1

    if active_only:
        where_clauses.append("is_active = true")

    where_sql = " AND ".join(where_clauses) if where_clauses else "true"

    # Note: `id::text` ensures Pydantic gets `id` as a string.
    select_sql = ", ".join(
        [
            "id::text AS id",
            "netxp_id",
            "is_active",
            "first_seen_at",
            "last_seen_at",
            "inactive_since",
            *[c for c in _TYPED_COLUMNS],
        ]
    )

    conn = await connect()
    try:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM netxp_members WHERE {where_sql}", *params_base)

        limit_param_idx = param_idx
        offset_param_idx = param_idx + 1
        params = [*params_base, page_size, offset]

        items_sql = f"""
            SELECT {select_sql}
            FROM netxp_members
            WHERE {where_sql}
            ORDER BY nachname NULLS LAST, vorname NULLS LAST, netxp_id
            LIMIT ${limit_param_idx}
            OFFSET ${offset_param_idx}
        """

        rows = await conn.fetch(items_sql, *params)

        items: list[MemberOut] = []
        for r in rows:
            items.append(
                MemberOut(
                    id=r["id"],
                    netxp_id=r["netxp_id"],
                    is_active=bool(r["is_active"]),
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                    inactive_since=r["inactive_since"],
                    **{c: r[c] for c in _TYPED_COLUMNS},
                )
            )

        return {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
            "items": items,
        }
    finally:
        await conn.close()

