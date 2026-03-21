#!/usr/bin/env python3
"""
Diagnose GET /api/netxp-members: same-venv import/schema checks, HTTP probe, tail API err log.

Run from repo root (or anywhere), using the project venv:

  api\\.venv\\Scripts\\python.exe test_scripts\\diagnose_netxp_members_api.py --token YOUR_JWT

Get a JWT: log in as admin in the web app, then copy the full token (must be three segments
separated by dots: header.payload.signature). A string like "eyJhbGciOiJIUzI1NiIs..." alone
is only the header and will return 401 Invalid token. Copy cookie `tt_access_token` or the
full `Authorization: Bearer ...` value from DevTools Network, or set API_TEST_BEARER_TOKEN.

Backend routes have NO /api prefix. Vite (web/vite.config.ts) rewrites /api -> '' when proxying
to port 8000, so the browser calls /api/netxp-members but uvicorn serves /netxp-members only.

Use --via-vite to hit http://127.0.0.1:5173/api/... like the browser; default is direct :8000/netxp-members.

"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "api"
ERR_LOG = REPO_ROOT / "logs" / "dev-start-all-api.err.log"


def _ensure_api_on_path() -> None:
    ap = str(API_DIR)
    if ap not in sys.path:
        sys.path.insert(0, ap)


def static_checks() -> None:
    _ensure_api_on_path()
    import app.netxp_members.router as router_mod  # noqa: PLC0415

    from app.netxp_members.models import NetxpMemberOut  # noqa: PLC0415
    from app.netxp_members.router import list_netxp_members  # noqa: PLC0415

    print("--- static (same sys.path as script; must match API if venv + cwd match) ---")
    print("router module file:", inspect.getfile(router_mod))
    try:
        lines, start = inspect.getsourcelines(list_netxp_members)
        end = start + len(lines) - 1
        print(f"list_netxp_members source lines (approx): {start}-{end}")
    except OSError as e:
        print("getsourcelines(list_netxp_members):", e)
    schema = NetxpMemberOut.model_json_schema()["properties"].get("mitgliedsnummer")
    print("NetxpMemberOut mitgliedsnummer JSON schema fragment:", json.dumps(schema, indent=2))


def http_get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=60) as resp:
        return int(resp.status), resp.read()


def _jwt_looks_complete(t: str) -> bool:
    parts = t.split(".")
    return len(parts) == 3 and all(len(p) > 0 for p in parts)


def tail_file(path: Path, *, max_lines: int) -> None:
    print(f"--- tail {path} (last {max_lines} lines) ---")
    if not path.is_file():
        print(f"(file missing: {path})")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for line in lines[-max_lines:]:
        print(line)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Diagnose netxp members list (backend path /netxp-members; Vite uses /api/netxp-members)."
    )
    p.add_argument(
        "--via-vite",
        action="store_true",
        help="Call http://127.0.0.1:5173/api/netxp-members (same as browser) instead of direct :8000.",
    )
    p.add_argument("--base-url", default=os.environ.get("API_TEST_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument(
        "--token",
        default=os.environ.get("API_TEST_BEARER_TOKEN", ""),
        help="Admin JWT (or set API_TEST_BEARER_TOKEN)",
    )
    p.add_argument("--tail-lines", type=int, default=120)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--page-size", type=int, default=50)
    p.add_argument("--active-only", action="store_true", default=True)
    p.add_argument("--no-active-only", action="store_false", dest="active_only")
    p.add_argument("--current-members-only", action="store_true", default=True)
    p.add_argument("--no-current-members-only", action="store_false", dest="current_members_only")
    p.add_argument("--youth-only", action="store_true", default=False)
    p.add_argument("--sort-by", default="mitgliedsnummer")
    p.add_argument("--sort-dir", default="asc")
    args = p.parse_args()

    static_checks()

    base = args.base_url.rstrip("/")
    health_url = f"{base}/health"

    print("--- HTTP /health ---")
    try:
        code, body = http_get(health_url, {})
        print("status:", code)
        print(body[:2000].decode("utf-8", errors="replace"))
    except URLError as e:
        print("FAILED:", e)
        print("Is the API running? (e.g. scripts/dev-start-all.ps1)")
        tail_file(ERR_LOG, max_lines=args.tail_lines)
        return 1

    token = (args.token or "").strip()
    if not token:
        print("--- skip /api/netxp-members (no --token / API_TEST_BEARER_TOKEN) ---")
        tail_file(ERR_LOG, max_lines=args.tail_lines)
        return 0

    if not _jwt_looks_complete(token):
        print(
            "WARNING: Token does not look like a complete JWT (need three dot-separated parts). "
            "If you only see one long base64 segment, that is the header — copy the full "
            "tt_access_token cookie or the entire Bearer value after login."
        )

    q = {
        "page": args.page,
        "page_size": args.page_size,
        "active_only": str(args.active_only).lower(),
        "current_members_only": str(args.current_members_only).lower(),
        "youth_only": str(args.youth_only).lower(),
        "sort_by": args.sort_by,
        "sort_dir": args.sort_dir,
    }
    if args.via_vite:
        vite_base = os.environ.get("API_TEST_VITE_URL", "http://127.0.0.1:5173").rstrip("/")
        members_url = f"{vite_base}/api/netxp-members?{urlencode(q)}"
    else:
        # Direct to uvicorn: no /api prefix (see web/vite.config.ts proxy rewrite).
        members_url = f"{base}/netxp-members?{urlencode(q)}"
    headers = {"Authorization": f"Bearer {token}"}

    print("--- HTTP GET netxp-members (admin) ---")
    print("URL:", members_url)
    try:
        code, body = http_get(members_url, headers)
        print("status:", code)
        txt = body.decode("utf-8", errors="replace")
        try:
            data = json.loads(txt)
            print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])
            if len(txt) > 4000:
                print("... (truncated)")
        except json.JSONDecodeError:
            print(txt[:4000])
    except HTTPError as e:
        print("status:", e.code)
        err_body = e.read() if e.fp else b""
        print(err_body[:4000].decode("utf-8", errors="replace"))
    except URLError as e:
        print("FAILED:", e)

    tail_file(ERR_LOG, max_lines=args.tail_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
