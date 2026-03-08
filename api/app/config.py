"""Load environment and expose config. .env is read from project root (parent of api/)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Support: project root .env (local), parent .env, or parent/env/api.env (staging)
for path in (
    Path.cwd() / ".env",
    Path.cwd().parent / ".env",
    Path.cwd().parent / "env" / "api.env",
):
    if path.exists():
        load_dotenv(path)
        break

DATABASE_URL = os.getenv("DATABASE_URL", "")
