# Treptower Teufel Club App

Member and admin backend + frontend for the club. FastAPI (API), Vite + Svelte (web), PostgreSQL.

## Docs (start here)

| Doc | Purpose |
|-----|--------|
| [docs/philosophy.md](docs/philosophy.md) | What we build and why (product, architecture, tech choices) |
| [docs/local-dev-setup.md](docs/local-dev-setup.md) | Get the app running on your machine |
| [docs/deploy.md](docs/deploy.md) | Deploy scripts, staging/prod |
| [docs/github-actions.md](docs/github-actions.md) | CI secrets, staging/prod workflows |
| [docs/staging-setup.md](docs/staging-setup.md) | Staging server reference (Hetzner, SSH, DB) |
| [docs/server-layout.md](docs/server-layout.md) | **Canonical** server paths: staging + prod, ports, DBs |
| [docs/plan-staging-prod-github-deploy.md](docs/plan-staging-prod-github-deploy.md) | Checklist: prod, GitHub deploy, migration |
| [docs/env-and-secrets.md](docs/env-and-secrets.md) | Where to put `.env` and secrets |
| [scripts/README.md](scripts/README.md) | run-api, commit-and-push, ssh-staging, deploy-staging |

## Repo layout

- **api/** — FastAPI backend
- **web/** — Vite + Svelte frontend
- **docs/** — Philosophy, setup, deploy, Caddy, systemd
- **ops/** — systemd unit files (for staging)
- **scripts/** — Helper scripts (deploy, SSH, commit-push)

## Quick start (local)

1. Clone, then see [docs/local-dev-setup.md](docs/local-dev-setup.md).
2. API: `cd api && python -m venv .venv && pip install -e .` (activate venv first on Windows), then from repo root `.\scripts\run-api.ps1` (or `api/.venv/bin/python -m uvicorn app.main:app --reload --app-dir api` on Unix).
3. Web: `cd web && npm install && npm run dev`.
4. Staging deploy: `.\scripts\deploy-staging.ps1` (after first-time server setup in deploy.md).
