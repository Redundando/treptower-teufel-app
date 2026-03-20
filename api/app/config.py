"""Load environment + TOML configs and expose a namespaced `CONFIG`.

Secrets come from `.env` (loaded from project root / staging parent dirs).
Defaults come from `api/app/config/**/*.toml`.

Usage:
- `CONFIG["app"]` holds values from `config/app.toml`
- `CONFIG["features"][<feature>]` holds values from `config/features/<feature>.toml`
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

__all__ = ["CONFIG", "reload_config"]

CONFIG: dict[str, Any] = {}


def _load_dotenv_files() -> None:
    # Support: project root .env (local), parent .env, or parent/env/api.env (staging)
    for path in (
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path.cwd().parent / "env" / "api.env",
    ):
        if path.exists():
            load_dotenv(path)
            break


def _load_toml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Missing config TOML: {path}")
    with path.open("rb") as f:
        return tomllib.load(f)


def _set_nested_value(tree: dict[str, Any], path_segments: list[str], value: Any) -> None:
    if not path_segments:
        raise RuntimeError("Internal error: empty config path")
    cursor: dict[str, Any] = tree
    for seg in path_segments[:-1]:
        existing = cursor.get(seg)
        if existing is None:
            cursor[seg] = {}
            cursor = cursor[seg]  # type: ignore[assignment]
            continue
        if not isinstance(existing, dict):
            raise RuntimeError(f"Config path collision at segment `{seg}`")
        cursor = existing
    cursor[path_segments[-1]] = value


def _load_all_toml_configs(config_dir: Path) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    for path in sorted(config_dir.rglob("*.toml")):
        rel = path.relative_to(config_dir)
        segments = list(rel.parts)
        segments[-1] = Path(segments[-1]).stem
        parsed = _load_toml_file(path)
        _set_nested_value(tree, segments, parsed)
    return tree


def _apply_env_overrides_to_app_config(app_cfg: dict[str, Any]) -> None:
    """Override leaves under `app_cfg` based on env var names derived from the key path.

    Example:
      app_cfg["jwt"]["access_token_seconds"] -> env var `JWT_ACCESS_TOKEN_SECONDS`
      app_cfg["database"]["url"] -> env var `DATABASE_URL`
    """

    def walk(cursor: dict[str, Any], path_prefix: list[str]) -> None:
        for key, value in cursor.items():
            next_prefix = [*path_prefix, key]
            if isinstance(value, dict):
                walk(value, next_prefix)
                continue

            env_key = "_".join(s.upper() for s in next_prefix)
            raw = os.getenv(env_key)
            if raw is None:
                continue

            # Preserve types by casting based on the current value's type.
            if isinstance(value, bool):
                cursor[key] = raw.strip().lower() in {"1", "true", "yes", "on"}
            elif isinstance(value, int) and not isinstance(value, bool):
                cursor[key] = int(raw.strip())
            elif isinstance(value, str):
                cursor[key] = raw.strip()
            else:
                cursor[key] = raw

    walk(app_cfg, [])


def _validate_config_shape(cfg: dict[str, Any]) -> None:
    if "app" not in cfg:
        raise RuntimeError("Missing config section `app` (expected config/app.toml)")
    if "jwt" not in cfg["app"]:
        raise RuntimeError("Missing config section `app.jwt` (expected [jwt] in config/app.toml)")
    if "database" not in cfg["app"]:
        raise RuntimeError(
            "Missing config section `app.database` (expected [database] in config/app.toml)"
        )
    jwt_cfg = cfg["app"]["jwt"]
    if not isinstance(jwt_cfg, dict):
        raise RuntimeError("Config key `app.jwt` must be a table/dict")
    for required_key in ("algorithm", "access_token_seconds", "token_type", "secret_key"):
        if required_key not in jwt_cfg:
            raise RuntimeError(f"Missing required JWT key `{required_key}` in config/app.toml")


def reload_config() -> None:
    """(Re)load TOML defaults and apply `.env` overrides."""
    global CONFIG

    _load_dotenv_files()

    config_dir = Path(__file__).resolve().parent / "config"
    loaded = _load_all_toml_configs(config_dir)
    if "app" in loaded and isinstance(loaded["app"], dict):
        _apply_env_overrides_to_app_config(loaded["app"])

    _validate_config_shape(loaded)
    CONFIG = loaded


# Load at import time so config is available immediately.
reload_config()
