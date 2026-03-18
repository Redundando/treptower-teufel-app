#!/usr/bin/env bash
# Backward-compatible entry: delegates to deploy-remote-staging.sh.
# Run from repo root after cd, or via deploy-staging which cds to repo first.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/deploy-remote-staging.sh"
