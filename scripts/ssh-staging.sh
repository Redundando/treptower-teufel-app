#!/usr/bin/env bash
# SSH into staging server (arved@tttc-staging-01).
# Usage: ./scripts/ssh-staging.sh
# Override key: TTTC_SSH_KEY=~/.ssh/other_key ./scripts/ssh-staging.sh

KEY="${TTTC_SSH_KEY:-$HOME/.ssh/teufel_ed25519}"
HOST="46.225.208.231"
USER="arved"

exec ssh -i "$KEY" "${USER}@${HOST}" "$@"
