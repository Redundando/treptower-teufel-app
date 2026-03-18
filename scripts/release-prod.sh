#!/usr/bin/env bash
# Usage: ./scripts/release-prod.sh 0.1.0
set -euo pipefail
cd "$(dirname "$0")/.."
VER="${1:-}"
VER="${VER#v}"
if [[ ! "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: $0 0.1.0"
  exit 1
fi
TAG="v$VER"
if [ -n "$(git status --short)" ]; then
  echo "Working tree not clean."
  exit 1
fi
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG exists."
  exit 1
fi
git tag "$TAG"
git push origin "$TAG"
echo "Pushed $TAG — prod workflow should run."
