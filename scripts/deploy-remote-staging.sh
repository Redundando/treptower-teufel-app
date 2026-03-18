#!/usr/bin/env bash
# Run ON the server from repo checkout (staging). Pulls main, syncs api/web, restarts services.
# Repo layout: .../staging/repo or legacy .../app/repo; APP_ROOT is parent of repo/.
# See docs/server-layout.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

if [ ! -d "$REPO_ROOT/.git" ]; then
  echo "Not a git repo: $REPO_ROOT"
  exit 1
fi

cd "$REPO_ROOT"
echo "=== Staging: pull main ==="
git fetch origin main
git checkout main
git pull origin main

if [ ! -d "$APP_ROOT/api/.venv" ]; then
  echo "Missing $APP_ROOT/api/.venv — create venv and pip install -e . first (see docs/deploy.md)."
  exit 1
fi

echo "=== Updating API (preserve .venv) ==="
(cd "$REPO_ROOT/api" && tar cf - .) | (cd "$APP_ROOT/api" && tar xf -)
cd "$APP_ROOT/api"
.venv/bin/pip install -e . -q

restart_api_only() {
  if [ -f /etc/systemd/system/tttc-api-staging.service ]; then
    echo "Restarting staging API (systemd)..."
    if sudo -n true 2>/dev/null; then
      sudo -n systemctl restart tttc-api-staging
    else
      echo "No passwordless sudo; falling back to nohup restart."
      pkill -f "uvicorn app.main:app" 2>/dev/null || true
      sleep 1
      mkdir -p "$APP_ROOT/logs"
      nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >> "$APP_ROOT/logs/api.log" 2>&1 &
    fi
  elif [ -f /etc/systemd/system/tttc-api.service ]; then
    echo "Restarting API (legacy systemd)..."
    if sudo -n true 2>/dev/null; then
      sudo -n systemctl restart tttc-api
    else
      echo "No passwordless sudo; falling back to nohup restart."
      pkill -f "uvicorn app.main:app" 2>/dev/null || true
      sleep 1
      mkdir -p "$APP_ROOT/logs"
      nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >> "$APP_ROOT/logs/api.log" 2>&1 &
    fi
  else
    echo "Stopping old API (if any)..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 1
    mkdir -p "$APP_ROOT/logs"
    nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >> "$APP_ROOT/logs/api.log" 2>&1 &
  fi
}

restart_api_only
echo "API on port 8000 (or via systemd)."

cd "$APP_ROOT"
echo "=== Updating web ==="
if [ ! -d "$REPO_ROOT/web" ]; then
  echo "repo/web not found. Commit and push web/, then pull again."
  exit 1
fi
rm -rf "$APP_ROOT/web"
cp -r "$REPO_ROOT/web" "$APP_ROOT/web"
cd "$APP_ROOT/web"
npm install --silent
npm run build

if [ -f /etc/systemd/system/tttc-web-staging.service ]; then
  echo "Restarting staging web (systemd)..."
  if sudo -n true 2>/dev/null; then
    sudo -n systemctl restart tttc-web-staging
  else
    echo "No passwordless sudo; falling back to nohup restart."
    pkill -f "vite preview" 2>/dev/null || true
    sleep 1
    mkdir -p "$APP_ROOT/logs"
    nohup npm run preview:staging >> "$APP_ROOT/logs/web.log" 2>&1 &
  fi
elif [ -f /etc/systemd/system/tttc-web.service ]; then
  if sudo -n true 2>/dev/null; then
    sudo -n systemctl restart tttc-web
  else
    echo "No passwordless sudo; falling back to nohup restart."
    pkill -f "vite preview" 2>/dev/null || true
    sleep 1
    mkdir -p "$APP_ROOT/logs"
    nohup npm run preview:staging >> "$APP_ROOT/logs/web.log" 2>&1 &
  fi
else
  echo "Stopping old frontend (if any)..."
  pkill -f "vite preview" 2>/dev/null || true
  sleep 1
  mkdir -p "$APP_ROOT/logs"
  nohup npm run preview:staging >> "$APP_ROOT/logs/web.log" 2>&1 &
fi
echo "Web preview on port 5173 (or via systemd)."

echo ""
echo "Done (staging)."
