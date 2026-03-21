# GitHub Actions deploy

Workflows live in **`.github/workflows/`**.

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| **Deploy staging** | Manual (**Actions → Run workflow**) | SSH to server → `git pull main` in staging repo → `scripts/deploy-remote-staging.sh` |
| **Deploy production** | Push tag **`v*.*.*`** (e.g. `v0.1.0`) | SSH → `GIT_REF=<tag>` → `scripts/deploy-remote-prod.sh` on **`/srv/tttc/prod`** |

---

## Repository secrets

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Example | Purpose |
|--------|---------|---------|
| **`SSH_HOST`** | `46.225.208.231` | Server IP or hostname |
| **`SSH_USER`** | `arved` | SSH login |
| **`SSH_PRIVATE_KEY`** | *(full PEM of deploy key or your key)* | Auth (prefer a **dedicated deploy** key with minimal rights) |

**Staging workflow** needs a repo at **`/srv/tttc/staging/repo`** *or* legacy **`/srv/tttc/app/repo`**.

**Prod workflow** needs **`/srv/tttc/prod`** fully provisioned (clone, venv, env, systemd `tttc-*-prod`) — see [plan-staging-prod-github-deploy.md](./plan-staging-prod-github-deploy.md).

---

## Local commands

| Goal | Command |
|------|---------|
| Push + SSH staging (no GitHub) | `.\scripts\deploy-staging.ps1` |
| Push + trigger staging workflow | `.\scripts\deploy-staging.ps1 -UseGitHub` (needs **`gh`** CLI logged in) |
| Release prod | `.\scripts\release-prod.ps1` (fetch + next patch tag) or `.\scripts\release-prod.ps1 0.1.0` (explicit); pushes tag → prod deploy |

**Before** manual staging workflow: **`git push origin main`** so the server pulls the commit you want.

---

## Security note

Anyone who can **push tags** matching `v*.*.*` can trigger prod deploy. When you add collaborators, tighten with branch/tag rules or GitHub Environments + required reviewers.
