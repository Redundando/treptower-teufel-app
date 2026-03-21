from __future__ import annotations

import json

import asyncpg

from app.config import CONFIG


def _require_database_url() -> str:
    url = (CONFIG["app"]["database"]["url"] or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


async def _init_jsonb_codec(conn: asyncpg.Connection) -> None:
    """
    asyncpg's default jsonb codec returns JSON as Python `str`. That broke `netxp_raw` anywhere
    we expected a `dict` without re-parsing. Decode to objects; encode dict/list with json.dumps.
    """
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )


async def connect() -> asyncpg.Connection:
    conn = await asyncpg.connect(_require_database_url())
    await _init_jsonb_codec(conn)
    return conn


async def create_pool(
    *,
    min_size: int = 1,
    max_size: int = 10,
) -> asyncpg.Pool:
    async def _init(conn: asyncpg.Connection) -> None:
        await _init_jsonb_codec(conn)

    return await asyncpg.create_pool(
        dsn=_require_database_url(),
        min_size=min_size,
        max_size=max_size,
        init=_init,
    )

