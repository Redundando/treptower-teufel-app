"""Verify netxp_members.mitgliedsnummer column type and sample values (BIGINT migration check).

Run from the repository root with the API venv and DATABASE_URL set (e.g. via .env):

  api\\.venv\\Scripts\\python.exe test_scripts/netxp_mitgliedsnummer_type_check.py

Optional:

  api\\.venv\\Scripts\\python.exe test_scripts/netxp_mitgliedsnummer_type_check.py --limit 10
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(_REPO_ROOT)
_API_DIR = _REPO_ROOT / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from app.db.connection import connect  # noqa: E402


def _cell(v: Any) -> str:
    if v is None:
        return "(null)"
    return str(v)


async def _run(*, limit: int) -> int:
    conn = await connect()
    try:
        type_row = await conn.fetchrow(
            """
            SELECT pg_typeof(mitgliedsnummer)::text AS typ
            FROM netxp_members
            LIMIT 1
            """
        )
        rows = await conn.fetch(
            """
            SELECT mitgliedsnummer, pg_typeof(mitgliedsnummer)::text AS pg_type
            FROM netxp_members
            ORDER BY netxp_id
            LIMIT $1
            """,
            limit,
        )
        stats = await conn.fetchrow(
            """
            SELECT
              COUNT(*)::bigint AS n_total,
              COUNT(mitgliedsnummer)::bigint AS n_nonnull,
              MIN(mitgliedsnummer) AS min_mn,
              MAX(mitgliedsnummer) AS max_mn
            FROM netxp_members
            """
        )
    finally:
        await conn.close()

    if type_row is None:
        print("(no rows in netxp_members — empty table)")
        return 0

    print(f"pg_typeof(mitgliedsnummer) from first row: {type_row['typ']}")
    print()
    print(f"Sample (first {len(rows)} rows by netxp_id):")
    print(f"{'mitgliedsnummer':>16}  {'pg_typeof':<20}")
    print(f"{'----------------':>16}  {'--------------------':<20}")
    for r in rows:
        print(f"{_cell(r['mitgliedsnummer']):>16}  {r['pg_type']:<20}")

    if stats:
        print()
        print(
            f"Stats: total_rows={stats['n_total']}  nonnull_mitgliedsnummer={stats['n_nonnull']}  "
            f"min={_cell(stats['min_mn'])}  max={_cell(stats['max_mn'])}"
        )

    expected = "bigint"
    if type_row["typ"] != expected:
        print()
        print(f"WARNING: expected column type `{expected}`, got `{type_row['typ']}`. Run migration 0004 if needed.")
        return 1

    print()
    print("OK: mitgliedsnummer is bigint.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Check netxp_members.mitgliedsnummer type and samples.")
    p.add_argument("--limit", type=int, default=5, help="Number of sample rows (default: 5).")
    args = p.parse_args()
    if args.limit < 1:
        p.error("--limit must be >= 1")
    return asyncio.run(_run(limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
