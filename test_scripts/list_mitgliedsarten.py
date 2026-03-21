"""List distinct mitgliedsart values (and row counts) from netxp_members.

Run from the repository root with the API venv:

  api/.venv/Scripts/python.exe test_scripts/list_mitgliedsarten.py
  api/.venv/Scripts/python.exe test_scripts/list_mitgliedsarten.py --active-only
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

import asyncpg  # noqa: E402

from app.db.connection import connect  # noqa: E402


def _cell(v: Any) -> str:
    if v is None:
        return "(null)"
    return str(v)


async def _run(*, active_only: bool) -> int:
    where = "WHERE is_active = true" if active_only else ""
    conn = await connect()
    try:
        rows = await conn.fetch(
            f"""
            SELECT mitgliedsart, COUNT(*)::bigint AS n
            FROM netxp_members
            {where}
            GROUP BY mitgliedsart
            ORDER BY mitgliedsart NULLS LAST
            """
        )
    finally:
        await conn.close()

    if not rows:
        print("(no rows in netxp_members)")
        return 0

    total = sum(int(r["n"]) for r in rows)
    w = max(len("mitgliedsart"), *(len(_cell(r["mitgliedsart"])) for r in rows))
    print(f"{'mitgliedsart'.ljust(w)}  count")
    print(f"{'-' * w}  -----")
    for r in rows:
        print(f"{_cell(r['mitgliedsart']).ljust(w)}  {int(r['n'])}")
    print(f"\n{len(rows)} distinct value(s), {total} row(s) total")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Distinct mitgliedsart + counts in netxp_members.")
    p.add_argument(
        "--active-only",
        action="store_true",
        help="Only count rows with is_active = true.",
    )
    args = p.parse_args(argv)
    try:
        return asyncio.run(_run(active_only=args.active_only))
    except Exception as e:
        print(f"list_mitgliedsarten failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
