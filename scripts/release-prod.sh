#!/usr/bin/env bash
# Create semver tag and push → GitHub Actions prod deploy.
# Usage:
#   ./scripts/release-prod.sh              # fetch origin, next patch from latest v*.*.* tag
#   ./scripts/release-prod.sh 0.1.0      # explicit version
#   SKIP_FETCH=1 ./scripts/release-prod.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${SKIP_FETCH:-}" != "1" ]]; then
  echo "Fetching from origin (tags)..."
  git fetch origin
fi

if [ -n "$(git status --short)" ]; then
  echo "Working tree not clean."
  exit 1
fi

if [[ $# -eq 0 ]]; then
  latest="$(git tag -l --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)"
  if [[ -z "$latest" ]]; then
    TAG="v0.1.0"
  else
    v="${latest#v}"
    IFS=. read -r major minor patch <<<"$v"
    TAG="v${major}.${minor}.$((patch + 1))"
  fi
  echo "No version passed — using next patch: $TAG"
else
  VER="${1#v}"
  if [[ ! "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Usage: $0 [0.1.0]   (optional semver; omit for auto patch bump)"
    exit 1
  fi
  TAG="v$VER"
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists (after fetch)."
  exit 1
fi

git tag "$TAG"
git push origin "$TAG"
echo "Pushed $TAG — prod workflow should run."
