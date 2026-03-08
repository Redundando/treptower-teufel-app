#!/usr/bin/env bash
# Deploy to staging: push local main, then SSH to server and run the remote deploy script.
# Prerequisite: First-time setup (clone, env, firewall) done once on the server (see docs/deploy.md).
# Usage: ./scripts/deploy-staging.sh
# Optional: SKIP_PUSH=1 ./scripts/deploy-staging.sh

set -e
cd "$(dirname "$0")/.."

if [ -z "$SKIP_PUSH" ]; then
  if [ -n "$(git status --short)" ]; then
    echo "You have uncommitted changes. Commit and push first, or run SKIP_PUSH=1 $0"
    exit 1
  fi
  echo "Pushing main..."
  git push origin main
fi

KEY="${TTTC_SSH_KEY:-$HOME/.ssh/teufel_ed25519}"
HOST="46.225.208.231"
USER="arved"

ssh -i "$KEY" "${USER}@${HOST}" "cd /srv/tttc/app/repo && git pull origin main && bash scripts/staging-deploy-remote.sh"
