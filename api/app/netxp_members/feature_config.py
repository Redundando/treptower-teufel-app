"""Load feature knobs for admin list/export from TOML (`config/features/netxp_members.toml`).

Note: `app.config.reload_config` only applies `.env` overrides to `CONFIG["app"]`, not `features/*`.
Change values here (or extend config loading) if you need env-based overrides for this feature.
"""

from __future__ import annotations

from typing import Any

from app.config import CONFIG


def netxp_members_settings() -> dict[str, Any]:
    return CONFIG["features"]["netxp_members"]
