from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from openpyxl import Workbook

from app.db.connection import connect
from app.netxp_members.columns import ALLOWED_VISUAL_EXPORT_COL_IDS, EXPORT_FIELDNAMES, TYPED_COLUMNS
from app.netxp_members.feature_config import netxp_members_settings
from app.netxp_members.query import (
    netxp_members_order_sql,
    netxp_members_where_sql_and_params,
    select_members_row_sql,
)
from app.netxp_members.serialization import row_netxp_raw


def normalize_export_columns(values: list[str] | None) -> list[str] | None:
    """If empty/None, caller uses legacy full export. Otherwise dedupe, preserve order, allowlist only."""
    if not values:
        return None
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        s = (raw or "").strip()
        if not s or s not in ALLOWED_VISUAL_EXPORT_COL_IDS:
            continue
        k = s.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out if out else None


def full_calendar_years_between(from_date: date, to_date: date) -> int:
    years = to_date.year - from_date.year
    if (to_date.month, to_date.day) < (from_date.month, from_date.day):
        years -= 1
    return max(0, years)


def as_date_only(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None


def mitgliedsnummer_for_export(v: Any) -> int | str | None:
    """Membership number as int for CSV/XLSX when numeric; non-digit text preserved as str."""
    if v is None:
        return None
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    s = str(v).strip()
    if not s:
        return None
    return int(s) if s.isdigit() else s


def project_export_row(full: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    """Map full DB export row to visible-column ids (active/age/member_years aligned with web table)."""
    out: dict[str, Any] = {}
    today = date.today()
    for col in columns:
        if col == "active":
            out["active"] = full["is_active"]
        elif col == "age":
            ge = as_date_only(full.get("geburtsdatum"))
            out["age"] = "" if ge is None else full_calendar_years_between(ge, today)
        elif col == "member_years":
            ej = as_date_only(full.get("eintrittsdatum"))
            out["member_years"] = "" if ej is None else full_calendar_years_between(ej, today)
        elif col == "mitgliedsnummer":
            out["mitgliedsnummer"] = mitgliedsnummer_for_export(full.get("mitgliedsnummer"))
        elif col in full:
            out[col] = full[col]
    return out


def prepare_export_rows(
    raw_rows: list[dict[str, Any]], columns: list[str] | None
) -> tuple[list[dict[str, Any]], list[str]]:
    cols_norm = normalize_export_columns(columns)
    fieldnames = list(EXPORT_FIELDNAMES)
    if cols_norm is None:
        rows_out: list[dict[str, Any]] = []
        for r in raw_rows:
            row = dict(r)
            if "mitgliedsnummer" in fieldnames:
                row["mitgliedsnummer"] = mitgliedsnummer_for_export(row.get("mitgliedsnummer"))
            rows_out.append(row)
        return rows_out, fieldnames
    return [project_export_row(r, cols_norm) for r in raw_rows], cols_norm


def export_row_dict(r: Any) -> dict[str, Any]:
    raw = row_netxp_raw(r["netxp_raw"])
    return {
        "id": r["id"],
        "netxp_id": r["netxp_id"],
        "is_active": r["is_active"],
        "first_seen_at": r["first_seen_at"],
        "last_seen_at": r["last_seen_at"],
        "inactive_since": r["inactive_since"],
        **{c: r[c] for c in TYPED_COLUMNS},
        "netxp_raw_json": json.dumps(raw, ensure_ascii=False),
    }


async def fetch_netxp_members_export_rows(
    *,
    search_norm: str | None,
    active_only: bool,
    current_members_only: bool,
    youth_only: bool,
    csv_status_aktiv: bool = False,
    csv_status_passiv: bool = False,
    sort_by_norm: str | None,
    sort_dir_norm: str,
) -> list[dict[str, Any]]:
    cfg = netxp_members_settings()
    export_limit = int(cfg["export_row_limit"])

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

    limit_param_idx = param_idx
    params = [*params_base, export_limit]

    items_sql = f"""
        SELECT {select_sql}
        FROM netxp_members
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT ${limit_param_idx}
    """

    conn = await connect()
    try:
        rows = await conn.fetch(items_sql, *params)
    finally:
        await conn.close()

    return [export_row_dict(r) for r in rows]


def xlsx_cell_value(v: Any) -> Any:
    """Normalize DB/asyncpg values for openpyxl (no tz-aware datetimes; bool before int)."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return bytes(v).decode("utf-8", errors="replace")
    if isinstance(v, datetime):
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v
    if isinstance(v, date):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        return v
    return str(v)


def export_rows_to_xlsx_bytes(row_dicts: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    cfg = netxp_members_settings()
    sheet_title = str(cfg["xlsx_sheet_title"])
    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("openpyxl workbook has no active sheet")
    ws.title = sheet_title[:31] if len(sheet_title) > 31 else sheet_title
    ws.append(fieldnames)
    for row in row_dicts:
        ws.append([xlsx_cell_value(row.get(k)) for k in fieldnames])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def write_csv_response_body(row_dicts: list[dict[str, Any]], fieldnames: list[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for row in row_dicts:
        w.writerow(row)
    return buf.getvalue()


def export_content_disposition_csv() -> str:
    cfg = netxp_members_settings()
    name = str(cfg["export_csv_filename"])
    return f'attachment; filename="{name}"'


def export_content_disposition_xlsx() -> str:
    cfg = netxp_members_settings()
    name = str(cfg["export_xlsx_filename"])
    return f'attachment; filename="{name}"'
