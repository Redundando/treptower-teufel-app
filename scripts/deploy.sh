#!/usr/bin/env bash
# Unified SSH deploy: staging | prod [git_ref]. Delegates to deploy-staging.sh / deploy-prod.sh.
# See docs/deploy.md §4.
# Usage:
#   ./scripts/deploy.sh staging
#   SKIP_PUSH=1 ./scripts/deploy.sh staging
#   ./scripts/deploy.sh prod main
#   ./scripts/deploy.sh prod v0.1.2
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
TARGET="${1:-}"
shift || true
case "$TARGET" in
  staging)
    exec bash "$SCRIPT_DIR/deploy-staging.sh" "$@"
    ;;
  prod)
    exec bash "$SCRIPT_DIR/deploy-prod.sh" "$@"
    ;;
  *)
    echo "Usage: $0 staging|prod [prod_git_ref]" >&2
    echo "  staging — optional env: SKIP_PUSH=1" >&2
    echo "  prod    — optional ref (default: latest local v*.*.* tag); e.g. main, v0.1.2" >&2
    exit 1
    ;;
esac
