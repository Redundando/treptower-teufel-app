# Deploy

**Single place for everything about deploying the app.**  
Server and env details live in [staging-setup.md](./staging-setup.md) and [env-and-secrets.md](./env-and-secrets.md); this doc focuses on **what to do** and **where things go**.

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
| **App base path** | `/srv/tttc/app` |

**Deploy destinations:**

| What | Path on server |
|------|-----------------|
| Backend (API) | `/srv/tttc/app/api` |
| Frontend (web) | `/srv/tttc/app/web` |
| Env files | `/srv/tttc/app/env/` (e.g. `api.env`, `web.env`) — **not** in Git. |
| Logs | `/srv/tttc/app/logs` |

---

## 4. Current state (no deploy scripts yet)

As of now we have **no automated deploy scripts**. Deploy is **manual**: SSH in, pull (or clone), install deps if needed, restart the app if it’s running via systemd (once we add that).

Below is the intended flow and manual steps. When we add scripts (e.g. `ops/deploy/staging.sh` or similar), we’ll document them here and replace the manual steps.

---

## 5. Staging deploy — manual steps

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

## 6. Env and secrets on the server

- Env files live under **`/srv/tttc/app/env/`** (e.g. `api.env`).
- They are **created and edited on the server** (or via a secure deploy step), **never** committed.
- See [env-and-secrets.md](./env-and-secrets.md) for the pattern and [staging-setup.md](./staging-setup.md) for DB name/user (e.g. `tttc_staging`, `tttc_staging_user`).

---

## 7. Future: deploy scripts and production

- **Deploy scripts:** When we add them (e.g. under `ops/deploy/`), they will:
  - Pull from Git (or use a specific ref).
  - Sync `api/` and `web/` to `/srv/tttc/app/`.
  - Optionally install deps, run migrations, restart systemd services.
- **Production:** Will be documented in a separate section or doc (different server(s), DB, domains). Staging remains the reference for “how we deploy” until then.

---

## 8. Quick reference

| Action | Where to look |
|--------|----------------|
| Server IP, SSH, paths | [staging-setup.md](./staging-setup.md) |
| Env / secrets strategy | [env-and-secrets.md](./env-and-secrets.md) |
| Repo URL, branch | This doc §2 |
| Deploy target paths | This doc §3 |
| Manual deploy steps | This doc §5 |

---

*Update this doc whenever we add deploy scripts, change paths, or introduce production.*
