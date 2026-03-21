from __future__ import annotations

from typing import Any

from starlette.requests import Request

from app.db.connection import connect
from app.netxp_members.columns import NETXP_MEMBER_SORTABLE_DB, TYPED_COLUMNS
from app.netxp_members.feature_config import netxp_members_settings
from app.netxp_members.serialization import netxp_member_item_json_dict


def normalize_search(search: str | None) -> str | None:
    s = (search or "").strip()
    return s or None


def normalize_sort_by(sort_by: str | None) -> str | None:
    if sort_by is None:
        return None
    s = str(sort_by).replace("\ufeff", "").strip().lower()
    return s or None


def merge_sort_query(
    request: Request,
    *,
    sort_by: str | None,
    sort_dir: str,
) -> tuple[str | None, str]:
    """
    Prefer FastAPI Query() values; fall back to raw query string.
    Some proxies or clients omit oddly named params from dependency injection.
    """
    sb = normalize_sort_by(sort_by)
    if sb is None:
        raw = request.query_params.get("sort_by") or request.query_params.get("sortBy")
        sb = normalize_sort_by(raw)
    sd_in = (sort_dir or "asc").strip().lower()
    if sd_in not in ("asc", "desc"):
        sd_in = (
            (request.query_params.get("sort_dir") or request.query_params.get("sortDir") or "asc")
            .strip()
            .lower()
        )
    if sd_in not in ("asc", "desc"):
        sd_in = "asc"
    return sb, sd_in


def normalize_sort_dir(sort_dir: str | None) -> str:
    d = (sort_dir or "asc").strip().lower()
    return d if d in ("asc", "desc") else "asc"


def effective_csv_status_lower_sql() -> str:
    """
    Single expression for CSV status used in filters; mirrors web `netxpCsvStatusText`:
    typed `csv_status` if set, else `netxp_raw` Status / STATUS / status keys.
    """
    return (
        "LOWER(TRIM(COALESCE("
        "NULLIF(TRIM(COALESCE(csv_status, '')), ''), "
        "NULLIF(TRIM(COALESCE(netxp_raw->>'Status', '')), ''), "
        "NULLIF(TRIM(COALESCE(netxp_raw->>'STATUS', '')), ''), "
        "NULLIF(TRIM(COALESCE(netxp_raw->>'status', '')), ''), "
        "''"
        ")))"
    )


def netxp_members_where_sql_and_params(
    *,
    search_norm: str | None,
    active_only: bool,
    current_members_only: bool,
    youth_only: bool = False,
    csv_status_aktiv: bool = False,
    csv_status_passiv: bool = False,
) -> tuple[str, list[Any], int]:
    cfg = netxp_members_settings()
    where_clauses: list[str] = []
    params_base: list[Any] = []
    param_idx = 1

    if search_norm is not None:
        pattern = f"%{search_norm}%"
        eff_status = effective_csv_status_lower_sql()
        where_clauses.append(
            "("
            f"nachname ILIKE ${param_idx} OR "
            f"vorname ILIKE ${param_idx} OR "
            f"netxp_id ILIKE ${param_idx} OR "
            f"mitgliedsnummer::text ILIKE ${param_idx} OR "
            f"{eff_status} ILIKE ${param_idx}"
            ")"
        )
        params_base.append(pattern)
        param_idx += 1

    if active_only:
        where_clauses.append("is_active = true")

    if current_members_only:
        where_clauses.append("(austrittsdatum IS NULL OR austrittsdatum > CURRENT_DATE)")

    if youth_only:
        threshold = int(cfg["youth_age_threshold_years"])
        interval_years = threshold + 1
        where_clauses.append(
            "geburtsdatum IS NOT NULL "
            f"AND (geburtsdatum + interval '{interval_years} years') > date_trunc('year', CURRENT_DATE)::date"
        )

    if csv_status_aktiv or csv_status_passiv:
        norm = effective_csv_status_lower_sql()
        av = str(cfg["csv_status_aktiv_value"]).strip().lower()
        pv = str(cfg["csv_status_passiv_value"]).strip().lower()
        if csv_status_aktiv and csv_status_passiv:
            where_clauses.append(f"{norm} IN (${param_idx}, ${param_idx + 1})")
            params_base.extend([av, pv])
            param_idx += 2
        elif csv_status_aktiv:
            where_clauses.append(f"{norm} = ${param_idx}")
            params_base.append(av)
            param_idx += 1
        else:
            where_clauses.append(f"{norm} = ${param_idx}")
            params_base.append(pv)
            param_idx += 1

    where_sql = " AND ".join(where_clauses) if where_clauses else "true"
    return where_sql, params_base, param_idx


def netxp_members_order_sql(sort_by: str | None, sort_dir: str | None) -> str:
    """Stable sort: primary column + nachname, vorname, netxp_id."""
    tie = "nachname NULLS LAST, vorname NULLS LAST, netxp_id"
    if not sort_by:
        return tie

    key = sort_by.strip().lower()
    d = (sort_dir or "asc").strip().lower()
    asc = d == "asc"
    if d not in ("asc", "desc"):
        asc = True

    if key == "age":
        col = "geburtsdatum"
        # asc age = youngest first = later birthdates first
        sql_dir = "DESC" if asc else "ASC"
    elif key == "member_years":
        col = "eintrittsdatum"
        # asc = fewer years = joined more recently = later eintrittsdatum first
        sql_dir = "DESC" if asc else "ASC"
    elif key == "active":
        col = "is_active"
        sql_dir = "ASC" if asc else "DESC"
    elif key == "csv_status":
        col = effective_csv_status_lower_sql()
        sql_dir = "ASC" if asc else "DESC"
    elif key in NETXP_MEMBER_SORTABLE_DB:
        col = key
        sql_dir = "ASC" if asc else "DESC"
    else:
        return tie

    return f"{col} {sql_dir} NULLS LAST, {tie}"


def select_members_row_sql() -> str:
    """Shared SELECT list for list + export queries (note: `id::text` for string id)."""
    return ", ".join(
        [
            "id::text AS id",
            "netxp_id",
            "is_active",
            "first_seen_at",
            "last_seen_at",
            "inactive_since",
            *[c for c in TYPED_COLUMNS],
            "netxp_raw",
        ]
    )


async def fetch_netxp_members_page(
    *,
    page: int,
    page_size: int,
    search_norm: str | None,
    active_only: bool,
    current_members_only: bool,
    youth_only: bool,
    csv_status_aktiv: bool,
    csv_status_passiv: bool,
    sort_by_norm: str | None,
    sort_dir_norm: str,
) -> tuple[list[dict[str, Any]], int]:
    where_sql, params_base, param_idx = netxp_members_where_sql_and_params(
        search_norm=search_norm,
        active_only=active_only,
        current_members_only=current_members_only,
        youth_only=youth_only,
        csv_status_aktiv=csv_status_aktiv,
        csv_status_passiv=csv_status_passiv,
    )
    order_sql = netxp_members_order_sql(sort_by_norm, sort_dir_norm)
    select_sql = select_members_row_sql()

    conn = await connect()
    try:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM netxp_members WHERE {where_sql}", *params_base)

        limit_param_idx = param_idx
        offset_param_idx = param_idx + 1
        offset = (page - 1) * page_size
        params = [*params_base, page_size, offset]

        items_sql = f"""
            SELECT {select_sql}
            FROM netxp_members
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ${limit_param_idx}
            OFFSET ${offset_param_idx}
        """

        rows = await conn.fetch(items_sql, *params)
        items = [netxp_member_item_json_dict(r) for r in rows]
        return items, int(total or 0)
    finally:
        await conn.close()
