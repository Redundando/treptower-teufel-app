"""Compare typed NetXP date columns to values stored in netxp_raw (CLI diagnostic).

Run from the repository root with the API venv's Python (so dependencies match the app):

  api/.venv/Scripts/python.exe test_scripts/netxp_check_raw.py
  api/.venv/Scripts/python.exe test_scripts/netxp_check_raw.py --issues-only --limit 50
  api/.venv/Scripts/python.exe test_scripts/netxp_check_raw.py --sync-headers
  api/.venv/Scripts/python.exe test_scripts/netxp_check_raw.py --raw-keys
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(_REPO_ROOT)
_API_DIR = _REPO_ROOT / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import asyncpg  # noqa: E402

from app.db.connection import connect  # noqa: E402


def _cell(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _print_table(rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = {c: max(len(c), *(len(_cell(r.get(c))) for r in rows)) for c in columns}
    header = "  ".join(c.ljust(widths[c]) for c in columns)
    print(header)
    print("  ".join("-" * widths[c] for c in columns))
    for r in rows:
        print("  ".join(_cell(r.get(c)).ljust(widths[c]) for c in columns))


async def _cmd_members(*, conn: asyncpg.Connection, limit: int, issues_only: bool) -> None:
    params: list[Any] = [limit]
    issue_filter = ""
    if issues_only:
        issue_filter = """
          AND (
            (geburtsdatum IS NULL AND NULLIF(BTRIM(netxp_raw->>'Geburtsdatum'), '') IS NOT NULL)
            OR (eintrittsdatum IS NULL AND NULLIF(BTRIM(netxp_raw->>'Eintrittsdatum'), '') IS NOT NULL)
          )
        """
    sql = f"""
        SELECT
          netxp_id,
          vorname,
          nachname,
          geburtsdatum,
          eintrittsdatum,
          netxp_raw->>'Geburtsdatum' AS raw_geburtsdatum,
          netxp_raw->>'Eintrittsdatum' AS raw_eintrittsdatum
        FROM netxp_members
        WHERE is_active = true
        {issue_filter}
        ORDER BY nachname NULLS LAST, vorname NULLS LAST, netxp_id
        LIMIT $1
    """
    recs = await conn.fetch(sql, *params)
    rows = [dict(r) for r in recs]
    _print_table(
        rows,
        [
            "netxp_id",
            "vorname",
            "nachname",
            "geburtsdatum",
            "eintrittsdatum",
            "raw_geburtsdatum",
            "raw_eintrittsdatum",
        ],
    )
    print(f"\n({len(rows)} row(s))")


async def _cmd_sync_headers(*, conn: asyncpg.Connection) -> None:
    row = await conn.fetchrow(
        """
        SELECT id, status, finished_at, headers
        FROM netxp_sync_runs
        WHERE headers IS NOT NULL
        ORDER BY COALESCE(finished_at, started_at) DESC
        LIMIT 1
        """
    )
    if not row:
        print("No netxp_sync_runs row with headers found.")
        return
    print(f"sync_run id={row['id']} status={row['status']} finished_at={row['finished_at']}")
    headers = row["headers"]
    if isinstance(headers, str):
        headers = json.loads(headers)
    if not isinstance(headers, list):
        print(f"Unexpected headers type: {type(headers)}")
        return
    for i, h in enumerate(headers):
        mark = " <--" if h in ("Geburtsdatum", "Eintrittsdatum") else ""
        print(f"  {i + 1:3}: {h!r}{mark}")


async def _cmd_raw_keys(*, conn: asyncpg.Connection) -> None:
    row = await conn.fetchrow(
        """
        SELECT netxp_id, netxp_raw
        FROM netxp_members
        WHERE is_active = true AND netxp_raw IS NOT NULL
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
        """
    )
    if not row:
        print("No active member with netxp_raw.")
        return
    raw = row["netxp_raw"]
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict):
        print(f"Unexpected netxp_raw type: {type(raw)}")
        return
    keys = sorted(raw.keys())
    print(f"netxp_id={row['netxp_id']} — {len(keys)} key(s) in netxp_raw:\n")
    for k in keys:
        hint = ""
        lk = k.lower()
        if "geburt" in lk or "eintritt" in lk or "austritt" in lk or "datum" in lk:
            hint = "  (date-related)"
        print(f"  {k!r}{hint}")


async def _async_main(args: argparse.Namespace) -> int:
    conn = await connect()
    try:
        ran_extra = False
        if args.sync_headers:
            await _cmd_sync_headers(conn=conn)
            ran_extra = True
        if args.raw_keys:
            if ran_extra:
                print()
            await _cmd_raw_keys(conn=conn)
            ran_extra = True
        if not ran_extra:
            await _cmd_members(conn=conn, limit=args.limit, issues_only=args.issues_only)
    finally:
        await conn.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compare typed NetXP member dates to netxp_raw (DB must match app config / DATABASE_URL)."
    )
    p.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Max rows for the member table view (default: 25).",
    )
    p.add_argument(
        "--issues-only",
        action="store_true",
        help="Only rows where raw Geburtsdatum/Eintrittsdatum is non-empty but the typed DATE column is NULL.",
    )
    p.add_argument(
        "--sync-headers",
        action="store_true",
        help="Print CSV column headers from the latest netxp_sync_runs row.",
    )
    p.add_argument(
        "--raw-keys",
        action="store_true",
        help="Print sorted netxp_raw keys from one recent active member (spot renamed date columns).",
    )
    args = p.parse_args(argv)
    try:
        return asyncio.run(_async_main(args))
    except Exception as e:
        print(f"netxp_check_raw failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
