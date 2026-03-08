#!/usr/bin/env bash
# Runs ON the staging server. Pulls latest, updates API and web, restarts both.
# Called by deploy-staging.ps1 / deploy-staging.sh via SSH.
# Prerequisite: First-time setup done (docs/deploy.md §5 steps 1-3).
set -e
APP_ROOT="/srv/tttc/app"
if [ ! -d "$APP_ROOT/repo" ] || [ ! -d "$APP_ROOT/api/.venv" ]; then
  echo "First-time setup not done. Run docs/deploy.md §5 steps 1-3 on the server first."
  exit 1
fi
cd "$APP_ROOT"

echo "=== Pulling latest from main ==="
cd repo && git pull origin main && cd ..

echo "=== Updating API (preserve .venv) ==="
(cd repo/api && tar cf - .) | (cd "$APP_ROOT/api" && tar xf -)
cd "$APP_ROOT/api"
.venv/bin/pip install -e . -q
echo "Stopping old API (if any)..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1
mkdir -p "$APP_ROOT/logs"
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >> "$APP_ROOT/logs/api.log" 2>&1 &
echo "API started (port 8000)."

cd "$APP_ROOT"
echo "=== Updating web ==="
if [ ! -d "$APP_ROOT/repo/web" ]; then
  echo "repo/web not found. Ensure web/ is committed and pushed, then on server: cd /srv/tttc/app/repo && git pull origin main"
  exit 1
fi
rm -rf "$APP_ROOT/web"
cp -r repo/web "$APP_ROOT/web"
cd "$APP_ROOT/web"
npm install --silent
npm run build
echo "Stopping old frontend (if any)..."
pkill -f "vite preview" 2>/dev/null || true
sleep 1
nohup npm run preview:staging >> "$APP_ROOT/logs/web.log" 2>&1 &
echo "Frontend started (port 5173)."

echo ""
echo "Done. Give it a few seconds, then open http://46.225.208.231:5173"
