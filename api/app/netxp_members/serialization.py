from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.netxp_members.columns import TYPED_COLUMNS
from app.netxp_members.models import mitgliedsnummer_from_db


def netxp_list_json_default(o: Any) -> Any:
    """json.dumps default=… for list rows (no Pydantic)."""
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, uuid.UUID):
        return str(o)
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    if isinstance(o, (bytes, bytearray, memoryview)):
        return bytes(o).decode("utf-8", errors="replace")
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def row_netxp_raw(value: Any) -> dict[str, Any]:
    """asyncpg often returns JSONB as `str` (JSON text), not `dict`; only accepting dict hid all data."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        try:
            parsed: Any = json.loads(s)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    if isinstance(value, (bytes, bytearray, memoryview)):
        try:
            parsed = json.loads(bytes(value).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def netxp_member_item_json_dict(r: Any) -> dict[str, Any]:
    """Build JSON-safe row dict without importing NetxpMemberOut at runtime (no validation/serialization)."""
    raw = row_netxp_raw(r["netxp_raw"])
    item: dict[str, Any] = {
        "id": str(r["id"]),
        "netxp_id": r["netxp_id"],
        "is_active": bool(r["is_active"]),
        "first_seen_at": r["first_seen_at"],
        "last_seen_at": r["last_seen_at"],
        "inactive_since": r["inactive_since"],
        "netxp_raw": raw,
    }
    for c in TYPED_COLUMNS:
        item[c] = mitgliedsnummer_from_db(r[c]) if c == "mitgliedsnummer" else r[c]
    return json.loads(json.dumps(item, default=netxp_list_json_default, ensure_ascii=False))
