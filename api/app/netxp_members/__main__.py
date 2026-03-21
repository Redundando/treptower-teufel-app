"""CLI: python -m app.netxp_members [--dry-run] [...]"""

from __future__ import annotations

from app.netxp_members.sync import main

if __name__ == "__main__":
    raise SystemExit(main())
