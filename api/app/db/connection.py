from __future__ import annotations

import asyncpg

from app.config import CONFIG


def _require_database_url() -> str:
    url = (CONFIG["app"]["database"]["url"] or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


async def connect() -> asyncpg.Connection:
    return await asyncpg.connect(_require_database_url())


async def create_pool(
    *,
    min_size: int = 1,
    max_size: int = 10,
) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=_require_database_url(),
        min_size=min_size,
        max_size=max_size,
    )

