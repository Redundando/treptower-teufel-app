#!/usr/bin/env bash
# Start the FastAPI dev server from the repo root (loads root .env).
# Prerequisite: api/.venv (Unix layout: bin/python) and pip install -e . in api/
# Usage:
#   ./scripts/run-api.sh
#   ./scripts/run-api.sh --port 8001

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
PY="$REPO_ROOT/api/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Missing api/.venv (Unix). From api/: python3 -m venv .venv && . .venv/bin/activate && pip install -e ." >&2
  exit 1
fi
exec "$PY" -m uvicorn app.main:app --reload --app-dir api "$@"
