#!/usr/bin/env bash
# Deploy prod over SSH — same as scripts/deploy-prod.ps1
# Usage: ./scripts/deploy-prod.sh [v0.1.2]
set -euo pipefail
cd "$(dirname "$0")/.."
REF="${1:-}"
if [[ -z "$REF" ]]; then
  git fetch origin --tags
  REF="$(git tag -l --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)"
  if [[ -z "$REF" ]]; then
    echo "No v*.*.* tag found. Usage: $0 v0.1.0" >&2
    exit 1
  fi
  echo "Using latest semver tag: $REF"
fi
KEY="${TTTC_SSH_KEY:-$HOME/.ssh/teufel_ed25519}"
exec ssh -i "$KEY" arved@46.225.208.231 "bash -lc 'set -euo pipefail; cd /srv/tttc/prod/repo; export GIT_REF=$REF; exec bash scripts/deploy-remote-prod.sh'"
