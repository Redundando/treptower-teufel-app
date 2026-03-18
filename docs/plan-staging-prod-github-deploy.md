# Plan: Staging + prod + GitHub-driven deploy

Working checklist. **Goal:** two isolated environments on one server, **manual** staging deploy from GitHub, **prod deploy on semver tag push**, promotion = same commit that was on staging. Canonical paths: **[server-layout.md](./server-layout.md)**.

Tick items as you go. Adjust ordering if something blocks (e.g. DNS before Caddy).

---

## Phase A — Decisions (done)

- [x] One server; staging + prod; **two DBs** (`tttc_staging`, `tttc_prod`).
- [x] URLs: `staging-app` / `staging-api` / `app` / `api` on `treptower-teufel.de`.
- [x] Git: **`main`**, feature branches; **no** staging/prod branches; **prod = semver tag** on promoted commit.
- [x] Deploy: **GitHub Actions** run deploy script **from repo checkout on server** (Option B).
- [x] Staging deploy: **manual** workflow dispatch (not auto on every push).
- [x] Prod deploy: **push tag** → deploy that ref to prod.
- [x] Paths: flat **`/srv/tttc/staging/`** and **`/srv/tttc/prod/`**.

---

## Phase B — DNS

- [ ] **A (and AAAA if used)** for all four hostnames → server IPv4 (`46.225.208.231`):
  - `staging-app.treptower-teufel.de`
  - `staging-api.treptower-teufel.de`
  - `app.treptower-teufel.de`
  - `api.treptower-teufel.de`
- [ ] Wait for propagation; verify with `ping` / dig.

---

## Phase C — PostgreSQL (prod DB)

On server (as postgres superuser):

- [ ] Create **`tttc_prod_user`** with strong password (store only in prod `api.env`).
- [ ] Create **`tttc_prod`** owned by that user.
- [ ] Confirm staging DB **`tttc_staging`** unchanged.

---

## Phase D — Migrate staging from `/srv/tttc/app` → `/srv/tttc/staging`

*Skip if you already created layout under `staging/` from scratch.*

- [ ] Stop old services: `sudo systemctl stop tttc-api tttc-web` (or pkill if still nohup).
- [ ] `sudo mkdir -p /srv/tttc/staging && sudo chown arved:arved /srv/tttc/staging`
- [ ] Move or copy: `app/repo` → `staging/repo`, `app/api` → `staging/api`, `app/web` → `staging/web`, `app/env` → `staging/env`, `app/logs` → `staging/logs` (or re-clone `repo` under `staging/` and re-run pip/npm build — see deploy script pattern).
- [ ] Fix **`staging/env/api.env`** if paths inside files reference old dirs (usually none).
- [ ] Update **systemd** to **`tttc-api-staging`** / **`tttc-web-staging`** with paths from [server-layout.md](./server-layout.md) (ports 8000 / 5173).
- [ ] `daemon-reload`, enable, start; curl localhost 8000/5173.
- [ ] Update **Caddy** staging blocks to still point at **8000** / **5173** (unchanged if ports same).
- [ ] Smoke test HTTPS staging URLs.
- [ ] Optional: remove or archive `/srv/tttc/app` after confidence.

---

## Phase E — Prod tree (first time)

- [ ] `sudo mkdir -p /srv/tttc/prod && sudo chown arved:arved /srv/tttc/prod`
- [ ] `git clone <repo> /srv/tttc/prod/repo`
- [ ] `cd /srv/tttc/prod/repo && git fetch --tags && git checkout v0.1.0` (or whatever first tag)
- [ ] Copy/sync `api` from `repo/api`, create **`.venv`**, `pip install -e .`
- [ ] Create **`/srv/tttc/prod/env/api.env`** with **`DATABASE_URL`** → `tttc_prod` + prod-only secrets (JWT, etc.).
- [ ] Build **`web`**: sync from repo, `npm ci && npm run build`
- [ ] Add **systemd** **`tttc-api-prod`** (port **8001**) and **`tttc-web-prod`** (port **5174**).
- [ ] Start prod stack; `curl` localhost 8001 / 5174.

---

## Phase F — Caddy (prod vhosts)

- [ ] Extend **`/etc/caddy/Caddyfile`**: `app.treptower-teufel.de` → **5174** (+ `/api` rules if same as staging pattern); `api.treptower-teufel.de` → **8001**.
- [ ] `caddy validate` + reload.
- [ ] Browser test prod URLs.

---

## Phase G — GitHub Actions

In repo **`.github/workflows/`** (added in repo):

- [x] **`deploy-staging.yml`** — manual dispatch; SSH → `deploy-remote-staging.sh`
- [x] **`deploy-prod.yml`** — push tag `v*.*.*`; SSH → `deploy-remote-prod.sh`

Still to do on **GitHub**:

- [ ] **Secrets:** `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` — see [github-actions.md](./github-actions.md)

Server:

- [ ] **`deploy` user** or **`arved`**: passwordless sudo **only** for the exact `systemctl restart` lines needed, OR run services as user that can restart own units (narrow permissions).

---

## Phase H — Local one-liner scripts (PowerShell)

- [x] **`deploy-staging.ps1`** — `-UseGitHub` runs workflow; default still SSH.
- [x] **`release-prod.ps1`** / **`release-prod.sh`**
- [x] **`scripts/README.md`**, **`docs/github-actions.md`**

---

## Phase I — Repo script parity

- [x] **`deploy-remote-staging.sh`**, **`deploy-remote-prod.sh`**
- [x] **`staging-deploy-remote.sh`** → delegates to staging deploy script
- [x] **`docs/deploy.md`** updated

---

## Phase J — Docs and ops hygiene

- [ ] **`staging-setup.md`** — quick reference paths = `/srv/tttc/staging/...`.
- [ ] **`env-and-secrets.md`** — prod env path `/srv/tttc/prod/env/`.
- [ ] **`systemd-staging.md`** — rename or split into staging + prod unit install.
- [ ] **`caddy-staging.md`** — add prod blocks or link to “full Caddyfile” snippet in server-layout or new doc.
- [ ] **Prod backups:** e.g. daily `pg_dump` of `tttc_prod` (cron + off-server copy).

---

## Phase K — First real promotion

- [ ] Deploy staging via workflow; verify staging URLs.
- [ ] Tag the **same commit** that staging ran: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Confirm prod workflow runs; verify prod URLs and prod DB.

---

## Quick reference

| I want to… | Action |
|------------|--------|
| Update staging | Push to `main`, run **manual** “Deploy staging” workflow (or local script that triggers it). |
| Release prod | After staging looks good: **`.\scripts\release-prod.ps1 0.2.0`** (once script exists) → tag **`v0.2.0`** → prod deploy runs. |
| Paths / ports | [server-layout.md](./server-layout.md) |

---

*Edit this plan as steps complete or scope changes.*
