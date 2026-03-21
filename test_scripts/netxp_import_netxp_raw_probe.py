"""Probe `netxp_raw` during CSV import (parse) and as stored/read from PostgreSQL.

Run from the **repository root** with the API venv:

  api\\.venv\\Scripts\\python.exe test_scripts/netxp_import_netxp_raw_probe.py
  api\\.venv\\Scripts\\python.exe test_scripts/netxp_import_netxp_raw_probe.py --csv "C:\\path\\AlleMitglieder.csv"
  api\\.venv\\Scripts\\python.exe test_scripts/netxp_import_netxp_raw_probe.py --parse-only
  api\\.venv\\Scripts\\python.exe test_scripts/netxp_import_netxp_raw_probe.py --db-only

Requires `DATABASE_URL` for `--db-only` / default DB section. NetXP download needs the same
env as sync (`NETXP_AUTH` or `NETXP_CLUB_ID` + `NETXP_USERNAME` + `NETXP_PASSWORD`, etc.).
Put `.env` in the repo root (or set env vars) so `app.config` loads credentials.
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

from app.db.connection import connect  # noqa: E402
from app.netxp_members.sync import (  # noqa: E402
    _parse_csv_sync,
    download_and_parse_netxp_csv,
    load_netxp_sync_config,
)


def _summarize_parsed_raw(raw: dict[str, str], *, label: str) -> None:
    keys = sorted(raw.keys())
    print(f"  {label}: dict with {len(keys)} key(s)")
    if not keys:
        print("    (empty dict — check CSV headers / row parsing)")
        return
    preview = list(keys)[:12]
    print(f"    sample keys: {preview}")
    id_v = raw.get("ID", raw.get("Id", ""))
    print(f"    raw['ID'] (or Id) prefix: {id_v[:80]!r}" if id_v else "    raw['ID']: (missing)")
    blob = json.dumps(raw, ensure_ascii=False, sort_keys=True)
    print(f"    json.dumps(sort_keys=True) length: {len(blob)} bytes")


async def _probe_download(*, limit: int | None) -> None:
    cfg = load_netxp_sync_config()
    print("--- Parse: download + parse (same as sync import) ---")
    print(f"  URL: {cfg['members_csv_url'][:80]}{'…' if len(cfg['members_csv_url']) > 80 else ''}")
    res = await download_and_parse_netxp_csv(
        members_csv_url=cfg["members_csv_url"],
        auth_user=cfg["auth_user"],
        auth_password=cfg["auth_password"],
        timeout_seconds=cfg["timeout_seconds"],
        limit=limit,
    )
    print(f"  rows parsed: {len(res.parsed_rows)}  encoding: {res.encoding_used!r}")
    if not res.parsed_rows:
        print("  (no rows — nothing to show)")
        return
    pr0 = res.parsed_rows[0]
    print(f"  first row netxp_id: {pr0.netxp_id!r}")
    _summarize_parsed_raw(pr0.raw, label="first row pr.raw")


def _probe_local_csv(path: Path, *, limit: int | None) -> None:
    print("--- Parse: local CSV file ---")
    print(f"  file: {path}")
    encoding, headers, rows = _parse_csv_sync(csv_path=path, encoding="", limit=limit)
    print(f"  headers count: {len(headers)}  rows parsed: {len(rows)}  encoding: {encoding!r}")
    if headers:
        print(f"  first headers: {headers[:8]!r} …")
    if not rows:
        print("  (no data rows)")
        return
    _summarize_parsed_raw(rows[0].raw, label="first row pr.raw")


async def _probe_db(*, sample: int) -> None:
    print("--- Database: netxp_raw as returned by asyncpg ---")
    conn = await connect()
    try:
        rows = await conn.fetch(
            """
            SELECT netxp_id, netxp_raw, updated_at
            FROM netxp_members
            ORDER BY updated_at DESC NULLS LAST, netxp_id
            LIMIT $1
            """,
            sample,
        )
        if not rows:
            print("  (no rows in netxp_members)")
            return
        for r in rows:
            v: Any = r["netxp_raw"]
            print(f"  netxp_id={r['netxp_id']!r}  updated_at={r['updated_at']}")
            print(f"    Python type: {type(v).__module__}.{type(v).__name__}")
            print(f"    isinstance dict: {isinstance(v, dict)}  isinstance str: {isinstance(v, str)}")
            if isinstance(v, dict):
                print(f"    dict len: {len(v)}")
                if v:
                    k0 = next(iter(v))
                    print(f"    first key: {k0!r} -> {str(v[k0])[:60]!r}")
            elif isinstance(v, str):
                print(f"    str len: {len(v)}  prefix: {v[:120]!r}…")
                try:
                    parsed = json.loads(v)
                    print(f"    json.loads -> {type(parsed).__name__} len={len(parsed) if isinstance(parsed, dict) else 'n/a'}")
                except json.JSONDecodeError as e:
                    print(f"    json.loads failed: {e}")
            else:
                print(f"    repr prefix: {repr(v)[:200]}")

        # Server-side shape (independent of Python codec)
        stat = await conn.fetchrow(
            """
            SELECT
              COUNT(*) FILTER (WHERE netxp_raw = '{}'::jsonb) AS empty_object,
              COUNT(*) FILTER (WHERE netxp_raw IS NOT NULL AND netxp_raw <> '{}'::jsonb) AS nonempty,
              COUNT(*) AS total
            FROM netxp_members
            """
        )
        if stat:
            print("--- Database: JSONB aggregates ---")
            print(
                f"  rows with netxp_raw = {{}}: {stat['empty_object']}  "
                f"non-empty object: {stat['nonempty']}  total: {stat['total']}"
            )
    finally:
        await conn.close()


async def _async_main(args: argparse.Namespace) -> int:
    if not args.db_only:
        if args.csv:
            p = Path(args.csv).expanduser()
            if not p.is_file():
                print(f"CSV not found: {p}", file=sys.stderr)
                return 2
            _probe_local_csv(p, limit=args.limit)
        else:
            try:
                await _probe_download(limit=args.limit)
            except Exception as e:
                print(f"Download/parse failed: {e}", file=sys.stderr)
                print("Tip: use --csv path/to/AlleMitglieder.csv to skip download.", file=sys.stderr)
                if not args.db_only:
                    return 1

    if not args.parse_only:
        try:
            await _probe_db(sample=args.db_sample)
        except Exception as e:
            print(f"DB probe failed: {e}", file=sys.stderr)
            return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Probe netxp_raw at parse time and from PostgreSQL.")
    p.add_argument(
        "--csv",
        metavar="PATH",
        help="Parse this local CSV (semicolon-delimited, NetXP export) instead of downloading.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=5,
        metavar="N",
        help="Max CSV data rows to parse (default: 5).",
    )
    p.add_argument(
        "--parse-only",
        action="store_true",
        help="Only run CSV parse (download or --csv); skip database.",
    )
    p.add_argument(
        "--db-only",
        action="store_true",
        help="Only query netxp_members; skip CSV.",
    )
    p.add_argument(
        "--db-sample",
        type=int,
        default=3,
        metavar="N",
        help="How many DB rows to show (default: 3).",
    )
    args = p.parse_args(argv)
    if args.parse_only and args.db_only:
        print("Cannot use both --parse-only and --db-only", file=sys.stderr)
        return 2
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
