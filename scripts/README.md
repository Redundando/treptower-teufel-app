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

## Deploy (staging, prod, release)

**Canonical “which command when” table:** [docs/deploy.md §4](../docs/deploy.md#41-which-command-when-canonical).

Thin wrappers (SSH from your machine):

| Script | Purpose |
|--------|---------|
| **`deploy-staging.ps1`** / **`deploy-staging.sh`** | Push `main` (optional), run **`deploy-remote-staging.sh`** on the server, or **`-UseGitHub`** to trigger the Actions workflow |
| **`deploy-prod.ps1`** / **`deploy-prod.sh`** | Run **`deploy-remote-prod.sh`** with a **branch or tag** (e.g. `main`, `v0.1.2`) |
| **`release-prod.ps1`** / **`release-prod.sh`** | Create semver **tag** + push → CI runs **`deploy-remote-prod.sh`** |
| **`deploy.ps1`** / **`deploy.sh`** | Single entry: **`-DeployTo staging`** or **`-DeployTo prod -Ref main`** |

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

