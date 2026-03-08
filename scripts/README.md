# Scripts

Helper scripts for the repo. Run from the **project root** (or the script will change to it).

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

Deploy to staging: **push `main`** (unless you pass skip), then **SSH to the server** and run the remote deploy script, which pulls latest, updates API and web, and restarts both. **Prerequisite:** First-time setup on the server is done (see [docs/deploy.md](../docs/deploy.md) §5 steps 1–3).

**PowerShell (Windows):**
```powershell
.\scripts\deploy-staging.ps1
```
Skip the push step (e.g. you already pushed): `.\scripts\deploy-staging.ps1 -SkipPush`

**Bash:**
```bash
./scripts/deploy-staging.sh
```
Skip the push: `SKIP_PUSH=1 ./scripts/deploy-staging.sh`

The remote script lives in the repo at `scripts/staging-deploy-remote.sh`; the server runs it after `git pull`.

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
