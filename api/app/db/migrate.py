from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from app.db.connection import connect


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


@dataclass(frozen=True)
class Migration:
    filename: str
    sql: str
    checksum: str


def _load_migrations(directory: Path) -> list[Migration]:
    if not directory.exists():
        raise RuntimeError(f"Migrations directory not found: {directory}")

    paths = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".sql")
    migrations: list[Migration] = []
    for p in paths:
        sql = p.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        migrations.append(Migration(filename=p.name, sql=sql, checksum=checksum))
    return migrations


async def _ensure_schema_migrations(conn) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          filename TEXT PRIMARY KEY,
          checksum TEXT NOT NULL,
          applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


async def _already_applied(conn) -> dict[str, str]:
    rows = await conn.fetch("SELECT filename, checksum FROM schema_migrations")
    return {r["filename"]: r["checksum"] for r in rows}


async def run(*, dry_run: bool = False) -> int:
    migrations = _load_migrations(MIGRATIONS_DIR)
    if not migrations:
        print(f"No migrations found in {MIGRATIONS_DIR}")
        return 0

    conn = await connect()
    try:
        await _ensure_schema_migrations(conn)
        applied = await _already_applied(conn)

        pending: list[Migration] = []
        for m in migrations:
            if m.filename in applied:
                if applied[m.filename] != m.checksum:
                    raise RuntimeError(
                        "Migration checksum mismatch for "
                        f"{m.filename}. Refusing to proceed."
                    )
                continue
            pending.append(m)

        if not pending:
            print("Migrations: up to date.")
            return 0

        if dry_run:
            print("Dry-run. Pending migrations:")
            for m in pending:
                print(f"- {m.filename}")
            return 0

        for m in pending:
            print(f"Applying {m.filename}...")
            async with conn.transaction():
                await conn.execute(m.sql)
                await conn.execute(
                    "INSERT INTO schema_migrations(filename, checksum) VALUES($1, $2)",
                    m.filename,
                    m.checksum,
                )

        print(f"Applied {len(pending)} migration(s).")
        return 0
    finally:
        await conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply SQL migrations.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show pending migrations without applying.",
    )
    args = parser.parse_args(argv)

    try:
        import asyncio

        return asyncio.run(run(dry_run=args.dry_run))
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

