from __future__ import annotations

import argparse
import asyncio

from app.db.connection import connect
from app.auth.password import hash_password


async def seed_admin(*, email: str, password: str) -> None:
    email_norm = (email or "").strip().lower()
    password = password or ""
    if not email_norm or not password:
        raise ValueError("Both --email and --password are required")

    conn = await connect()
    try:
        user_count = await conn.fetchval("SELECT COUNT(*) FROM app_users")
        if user_count and int(user_count) > 0:
            raise RuntimeError("Refusing to seed admin: users already exist")

        # Create initial admin user.
        await conn.execute(
            """
            INSERT INTO app_users (email, password_hash, role)
            VALUES ($1, $2, 'admin')
            """,
            email_norm,
            hash_password(password),
        )

        print(f"Seeded initial admin user: {email_norm}")
    finally:
        await conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the initial admin user (one-time).")
    parser.add_argument("--email", required=True, help="Admin email (unique).")
    parser.add_argument("--password", required=True, help="Admin password (plaintext).")
    args = parser.parse_args(argv)

    try:
        asyncio.run(seed_admin(email=args.email, password=args.password))
        return 0
    except Exception as e:
        print(f"Seed failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

