# Deploy

**Single place for everything about deploying the app.**  
**Target server paths (staging + prod):** [server-layout.md](./server-layout.md). **Rollout checklist:** [plan-staging-prod-github-deploy.md](./plan-staging-prod-github-deploy.md).  
Server and env details: [staging-setup.md](./staging-setup.md), [env-and-secrets.md](./env-and-secrets.md).

---

## 1. Principle

- **Infrastructure** (OS, PostgreSQL, users, firewall, directories) → set up **manually** on the server.
- **Application** (api, web) → developed **locally**, in Git, and brought to the server **via deploy** (clone/pull + copy/run).

We do **not** commit secrets; we do **not** manually edit code on the server. We deploy from the repo.

---

## 2. Repo and branch

| Item | Value |
|------|--------|
| **Repo** | https://github.com/Redundando/treptower-teufel-app |
| **Default branch** | `main` |
| **Deploy source** | Clone or pull `main` (or a tagged commit when we add tags). |

---

## 3. Staging deploy target

| Item | Value |
|------|--------|
| **Server** | `tttc-staging-01` — see [staging-setup.md](./staging-setup.md) for full details. |
| **SSH** | `arved@46.225.208.231` with key `C:\Users\arved\.ssh\teufel_ed25519` |
| **App base path** | `/srv/tttc/staging` |

**Deploy destinations:**

| What | Path on server |
|------|-----------------|
| Backend (API) | `/srv/tttc/staging/api` |
| Frontend (web) | `/srv/tttc/staging/web` |
| Env files | `/srv/tttc/staging/env/` (e.g. `api.env`) — **not** in Git. |
| Logs | `/srv/tttc/staging/logs` |

**Legacy note:** older staging-only setups used `/srv/tttc/app/...`.

---

## 4. Deploy automation (current)

| What | Where |
|------|--------|
| **Staging (SSH from your PC)** | `.\scripts\deploy-staging.ps1` → runs `scripts/deploy-remote-staging.sh` on the server |
| **Staging (GitHub)** | Workflow **Deploy staging** (manual dispatch); secrets: [github-actions.md](./github-actions.md) |
| **Production** | Push semver tag → workflow **Deploy production**; local helper `.\scripts\release-prod.ps1 0.1.0` |

Remote scripts: **`scripts/deploy-remote-staging.sh`**, **`scripts/deploy-remote-prod.sh`**. Paths: [server-layout.md](./server-layout.md).

First-time server setup (clone, venv, env) is still partly **manual**; see §5 and [plan-staging-prod-github-deploy.md](./plan-staging-prod-github-deploy.md).

---

## 5. First deploy: “Hello world” on staging

Use this checklist once to get the API and frontend running on staging. **Prerequisite:** Latest code pushed to `main`; you have the staging DB password for `tttc_staging_user`.

**On your machine (once):** Push any uncommitted changes and ensure `main` is up to date.

**On the server (SSH in and run in order):**

1. **Dirs and clone**
   ```bash
   sudo mkdir -p /srv/tttc/staging
   sudo chown arved:arved /srv/tttc/staging
   cd /srv/tttc/staging
   git clone https://github.com/Redundando/treptower-teufel-app.git repo
   ```

2. **Open firewall for API and frontend**
   ```bash
   sudo ufw allow 8000/tcp
   sudo ufw allow 5173/tcp
   sudo ufw status
   ```

3. **API: copy, venv, env**
   ```bash
   cp -r repo/api /srv/tttc/staging/
   cd /srv/tttc/staging/api
   python3 -m venv .venv
   .venv/bin/python -m pip install -e .
   mkdir -p /srv/tttc/staging/env
   ```
   Create `/srv/tttc/staging/env/api.env` with one line (use your real staging DB password):
   ```bash
   echo 'DATABASE_URL=postgresql://tttc_staging_user:YOUR_STAGING_PASSWORD@localhost:5432/tttc_staging' | nano /srv/tttc/staging/env/api.env
   ```
   (Or edit with `nano /srv/tttc/staging/env/api.env` and paste the line.)

4. **Run API in the background**
   ```bash
   cd /srv/tttc/staging/api
   mkdir -p /srv/tttc/staging/logs
   nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /srv/tttc/staging/logs/api.log 2>&1 &
   ```
   Check: `curl -s http://localhost:8000/health` → `{"status":"ok"}`.

5. **Frontend: copy, install, build**
   ```bash
   cp -r repo/web /srv/tttc/staging/
   cd /srv/tttc/staging/web
   npm install
   npm run build
   ```

6. **Run frontend preview (serves `dist/` and proxies `/api` to the API)**
   ```bash
   cd /srv/tttc/staging/web
   mkdir -p /srv/tttc/staging/logs
   nohup npm run preview:staging > /srv/tttc/staging/logs/web.log 2>&1 &
   ```
   Check: `curl -s http://localhost:5173` → HTML.

7. **In your browser**
   Open **http://46.225.208.231:5173** — you should see “Hello, Treptower Teufel” and “API: ok”.

To stop later: `pkill -f "uvicorn app.main:app"` and `pkill -f "vite preview"` (or find PIDs with `ps aux | grep uvicorn` / `ps aux | grep vite`).

**After first-time setup:** Use the script to deploy updates from your machine: run **`.\scripts\deploy-staging.ps1`** (or `./scripts/deploy-staging.sh`). It pushes `main`, then SSHs to the server and runs pull + API update + web build + restart of both. See [scripts/README.md](../scripts/README.md).

---

## 6. Staging deploy — manual steps (reference)

**Note:** These steps describe the **legacy** staging-only layout under `/srv/tttc/app`. For the current layout use `/srv/tttc/staging` (see [server-layout.md](./server-layout.md)) and the deploy scripts/workflows in §4.

### First time (clone and one-time setup)

1. **SSH to staging**
   ```bash
   ssh -i C:\Users\arved\.ssh\teufel_ed25519 arved@46.225.208.231
   ```
2. **Ensure directory exists**
   ```bash
   sudo mkdir -p /srv/tttc/app
   sudo chown arved:arved /srv/tttc/app
   ```
3. **Clone repo** (e.g. into a temp or direct into place)
   ```bash
   cd /srv/tttc/app
   git clone https://github.com/Redundando/treptower-teufel-app.git repo
   ```
4. **Copy API into place**
   ```bash
   cp -r repo/api /srv/tttc/app/
   # Create venv and install deps (see api/README on server or below)
   cd /srv/tttc/app/api
   python3 -m venv .venv
   .venv/bin/pip install -e .
   ```
5. **Create env file on server** (not in Git)
   ```bash
   mkdir -p /srv/tttc/app/env
   # Create /srv/tttc/app/env/api.env with DATABASE_URL etc. (see env-and-secrets.md)
   ```
6. **Run API** (until we have systemd: run manually or in a terminal)
   ```bash
   cd /srv/tttc/app/api
   .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   (When Caddy + systemd exist, we’ll start/restart the service instead.)

### Later deploys (update code)

1. **SSH to staging** (same as above).
2. **Pull latest**
   ```bash
   cd /srv/tttc/app/repo
   git pull origin main
   ```
3. **Update API**
   ```bash
   cp -r /srv/tttc/app/repo/api /srv/tttc/app/
   cd /srv/tttc/app/api
   .venv/bin/pip install -e .   # if deps changed
   # Restart the app (manual process or systemd later)
   ```
4. **Update web** (when we have a frontend)
   ```bash
   cp -r /srv/tttc/app/repo/web /srv/tttc/app/
   # Build if needed, restart/serve
   ```

---

## 7. Env and secrets on the server

- Env files live under:
  - **Staging:** `/srv/tttc/staging/env/` (e.g. `api.env`)
  - **Prod:** `/srv/tttc/prod/env/` (e.g. `api.env`)
- They are **created and edited on the server** (or via a secure deploy step), **never** committed.
- See [env-and-secrets.md](./env-and-secrets.md) for the pattern and [staging-setup.md](./staging-setup.md) for DB name/user (e.g. `tttc_staging`, `tttc_staging_user`).

---

## 8. Future: deploy scripts and production

- **Deploy scripts:** When we add them (e.g. under `ops/deploy/`), they will:
  - Pull from Git (or use a specific ref).
  - Sync `api/` and `web/` to `/srv/tttc/app/`.
  - Optionally install deps, run migrations, restart systemd services.
- **Production:** Will be documented in a separate section or doc (different server(s), DB, domains). Staging remains the reference for “how we deploy” until then.

---

## 9. systemd (API + web as services, optional)

So the API and frontend start on boot and you can use `systemctl restart`. One-time setup on the server: **[docs/systemd-staging.md](./systemd-staging.md)**. After that, the deploy script will use `systemctl restart` instead of nohup.

## 10. Caddy (HTTPS on staging)

Once DNS for `staging-app` and `staging-api` points to the server, use Caddy for HTTPS. Step-by-step: **[docs/caddy-staging.md](./caddy-staging.md)**.

## 11. Quick reference

| Action | Where to look |
|--------|----------------|
| Server IP, SSH, paths | [staging-setup.md](./staging-setup.md) |
| Env / secrets strategy | [env-and-secrets.md](./env-and-secrets.md) |
| Repo URL, branch | This doc §2 |
| Deploy target paths | This doc §3 |
| Manual deploy steps | This doc §5 |
| systemd (optional) | [systemd-staging.md](./systemd-staging.md) |
| Caddy / HTTPS staging | [caddy-staging.md](./caddy-staging.md) |

---

## 12. Missing (next hardening steps)

These items are **not required** for the first hello-world deployment, but they are the usual next steps before real users and real data.

### 12.1 Production backups (strongly recommended)

- **Goal**: if something goes wrong (bug, migration, operator error), you can restore `tttc_prod`.
- **Minimum**:
  - daily `pg_dump` of `tttc_prod`
  - keep multiple days (e.g. 7–30)
  - copy off the server (S3/Backblaze/another host), otherwise “server dies” = “backup dies”
  - do at least one restore test

### 12.2 Database migrations / schema changes (future)

Right now we don’t use a migration tool. When we start changing the DB schema (tables/columns/indexes), we should add a repeatable mechanism (committed to Git) such as Alembic.

- **Rule of thumb**:
  - run migrations on **staging** first (`tttc_staging`)
  - promote the same commit/tag to prod
  - run migrations on **prod** (`tttc_prod`) as part of prod deploy (before restarting API)

### 12.3 Monitoring / alerts (future)

- disk space alerts (Postgres + logs)
- service health: `tttc-api-*`, `tttc-web-*`, `postgresql`, `caddy`
- basic uptime check against `/health`

### 12.4 Security / access hygiene (future)

- use a **dedicated deploy SSH key** for GitHub Actions (not a personal laptop key)
- keep sudoers minimal: allow only the exact `systemctl restart ...` commands needed for deploy
- when contributors join: protect `main` and restrict who can push tags that trigger prod deploy

*Update this doc whenever we add deploy scripts, change paths, or introduce production.*
