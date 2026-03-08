#!/usr/bin/env bash
# Add all changes, commit with message, push to origin main.
# Usage: ./scripts/commit-and-push.sh "Your commit message"
# Run from repo root (or script cd's to root).

set -e
cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
  echo "Usage: $0 \"Commit message\""
  exit 1
fi

git add -A
if [ -z "$(git status --short)" ]; then
  echo "Nothing to commit (working tree clean)."
  exit 0
fi
git commit -m "$1"
git push origin main
echo "Done: added, committed, pushed to main."
