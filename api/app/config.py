"""Load environment and expose config. .env is read from project root (parent of api/)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Support running from project root (cwd = .) or from api/ (cwd = api)
for path in (Path.cwd() / ".env", Path.cwd().parent / ".env"):
    if path.exists():
        load_dotenv(path)
        break

DATABASE_URL = os.getenv("DATABASE_URL", "")
