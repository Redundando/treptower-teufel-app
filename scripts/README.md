# Scripts

Helper scripts for the repo. Run from the **project root** (or the script will change to it).

## run-api

Start the API locally with **reload** and the root **`.env`** (via `--app-dir api`). Requires **`api/.venv`** and `pip install -e .` inside `api/` once.

**PowerShell (Windows):**
```powershell
.\scripts\run-api.ps1
```
Another port: `.\scripts\run-api.ps1 --port 8001`

**Bash (WSL / Linux / Mac):**
```bash
chmod +x scripts/run-api.sh   # once
./scripts/run-api.sh
```

---

## ssh-staging

SSH into the staging server (`arved@46.225.208.231`). Uses the key `~/.ssh/teufel_ed25519` by default.

**PowerShell (Windows):**
```powershell
.\scripts\ssh-staging.ps1
```
To use a different key: `$env:TTTC_SSH_KEY = "C:\path\to\key"; .\scripts\ssh-staging.ps1`

**Bash (WSL / Linux / Mac):**
```bash
./scripts/ssh-staging.sh
```
To use a different key: `TTTC_SSH_KEY=~/.ssh/other_key ./scripts/ssh-staging.sh`  
Any extra arguments are passed to `ssh` (e.g. `./scripts/ssh-staging.sh -L 8080:localhost:80`).

---

## deploy-staging

**Push `main`**, then either **SSH** deploy or **GitHub Actions** (manual workflow).

| Mode | Command |
|------|---------|
| SSH (default) | `.\scripts\deploy-staging.ps1` |
| Same, no push first | `.\scripts\deploy-staging.ps1 -SkipPush` |
| Trigger **Deploy staging** workflow | `.\scripts\deploy-staging.ps1 -UseGitHub` (needs `gh` CLI + repo secrets; see [docs/github-actions.md](../docs/github-actions.md)) |

**Bash:** `./scripts/deploy-staging.sh` · `SKIP_PUSH=1 ./scripts/deploy-staging.sh`

Server runs **`scripts/deploy-remote-staging.sh`** (staging repo under `/srv/tttc/staging/repo` or legacy `/srv/tttc/app/repo`). See [docs/deploy.md](../docs/deploy.md).

---

## release-prod

**Create semver tag + push** → GitHub Actions runs **`scripts/deploy-remote-prod.sh`** on the server (same as **deploy-prod** below, but triggered by the tag push).

Runs **`git fetch origin`** first so the next patch is based on remote tags (use **`-SkipFetch`** to skip). With **no version argument**, the script tags the next **patch** after the highest `v*.*.*` tag (or **`v0.1.0`** if none exist).

```powershell
.\scripts\release-prod.ps1
.\scripts\release-prod.ps1 0.1.0
```

**Bash:** `./scripts/release-prod.sh` · `./scripts/release-prod.sh 0.1.0` · `SKIP_FETCH=1 ./scripts/release-prod.sh`

---

## deploy-prod

**One-shot prod deploy over SSH** — runs **`scripts/deploy-remote-prod.sh`** on the server: checkout tag, sync **api** + **web**, **`pip install`**, **`npm install`**, **`npm run build`**, DB migrations, **`systemctl restart`** API + web, and (if passwordless sudo works) **refresh `ops/systemd/*.service`** from the repo.

Use this to redeploy an **existing** tag without creating a new one, or if you prefer not to use GitHub Actions.

```powershell
.\scripts\deploy-prod.ps1 v0.1.2
.\scripts\deploy-prod.ps1
```

No argument → **fetch tags** and deploy the **latest local `v*.*.*` tag** (may be **older than `main`** — use **`.\scripts\deploy-prod.ps1 main`** to ship whatever is on `main` without a new tag).

**Bash:** `./scripts/deploy-prod.sh` · `./scripts/deploy-prod.sh v0.1.2` · `./scripts/deploy-prod.sh main`

---

## commit-and-push

Add all changes, commit with a message, push to `origin main`.

**PowerShell (Windows):**
```powershell
.\scripts\commit-and-push.ps1 "Your commit message"
```

**Bash (WSL / Linux / Mac):**
```bash
chmod +x scripts/commit-and-push.sh   # once
./scripts/commit-and-push.sh "Your commit message"
```

If there’s nothing to commit, the script exits without error.

---

## seed-admin

Seeds the initial admin user (one-time), using the auth CLI module and `api/.venv`.

**PowerShell (Windows):**
```powershell
.\scripts\seed-admin.ps1 -email admin@yourdomain.tld -password 'your-plaintext-password'
```

---

## dev-start-all

Start the API and the frontend together for local development (start-only; no migrations/seed).

The script stops anything listening on the API/Web ports, then stops **Python processes running uvicorn** for `app.main:app` (the `--reload` parent can survive a port-only kill and keep serving stale code). You should not need to `Stop-Process` all `python.exe` manually.

**PowerShell (Windows):**
```powershell
.\scripts\dev-start-all.ps1
```

If port `8000` is already in use:
```powershell
.\scripts\dev-start-all.ps1 -ApiPort 8001
```

