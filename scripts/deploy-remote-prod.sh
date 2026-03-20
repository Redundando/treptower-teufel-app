#!/usr/bin/env bash
# Run ON the server for production. Checks out GIT_REF (semver tag), syncs api/web, restarts prod services.
# Prerequisite: /srv/tttc/prod layout, tttc_prod DB, systemd tttc-api-prod + tttc-web-prod.
# Set GIT_REF e.g. v0.1.0 (GitHub Actions sets this from the pushed tag).
set -euo pipefail

GIT_REF="${GIT_REF:-}"
if [ -z "$GIT_REF" ]; then
  echo "Set GIT_REF to the tag to deploy, e.g. export GIT_REF=v0.1.0"
  exit 1
fi

APP_ROOT="/srv/tttc/prod"
REPO_ROOT="$APP_ROOT/repo"

if [ ! -d "$REPO_ROOT/.git" ]; then
  echo "Prod repo missing: $REPO_ROOT (see docs/plan-staging-prod-github-deploy.md)"
  exit 1
fi

cd "$REPO_ROOT"
echo "=== Prod: checkout $GIT_REF ==="
git fetch origin
git fetch --tags
git checkout "$GIT_REF"

if [ ! -d "$APP_ROOT/api/.venv" ]; then
  echo "Missing $APP_ROOT/api/.venv — provision prod api once (venv + pip install -e .)."
  exit 1
fi

echo "=== Updating API ==="
(cd "$REPO_ROOT/api" && tar cf - .) | (cd "$APP_ROOT/api" && tar xf -)
cd "$APP_ROOT/api"
if [ ! -x .venv/bin/python ]; then
  echo "Missing venv python at $APP_ROOT/api/.venv/bin/python"
  exit 1
fi
.venv/bin/python -m pip install -e . -q

echo "=== Running DB migrations (prod) ==="
.venv/bin/python -m app.db.migrate

if [ ! -f /etc/systemd/system/tttc-api-prod.service ]; then
  echo "Install tttc-api-prod.service (ops/systemd/) first."
  exit 1
fi
echo "Restarting prod API..."
if [ "$(id -u)" -eq 0 ]; then
  systemctl restart tttc-api-prod
else
  if ! sudo -n systemctl restart tttc-api-prod; then
    echo "Failed to restart tttc-api-prod via sudo -n."
    echo "Diagnostics:"
    command -v systemctl || true
    ls -la /etc/systemd/system/tttc-api-prod.service || true
    sudo -l || true
    exit 1
  fi
fi

echo "=== Updating web ==="
if [ ! -d "$REPO_ROOT/web" ]; then
  echo "repo/web not found."
  exit 1
fi
rm -rf "$APP_ROOT/web"
cp -r "$REPO_ROOT/web" "$APP_ROOT/web"
cd "$APP_ROOT/web"
npm install --silent
npm run build

if [ ! -f /etc/systemd/system/tttc-web-prod.service ]; then
  echo "Install tttc-web-prod.service first."
  exit 1
fi
if [ "$(id -u)" -eq 0 ]; then
  systemctl restart tttc-web-prod
else
  if ! sudo -n systemctl restart tttc-web-prod; then
    echo "Failed to restart tttc-web-prod via sudo -n."
    echo "Diagnostics:"
    command -v systemctl || true
    ls -la /etc/systemd/system/tttc-web-prod.service || true
    sudo -l || true
    exit 1
  fi
fi

echo ""
echo "Done (prod @ $GIT_REF)."
