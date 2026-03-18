# Server layout (canonical)

**Single source of truth** for paths on the Hetzner box: **staging** and **prod** side by side, **flat** directories under `/srv/tttc/`.

Related: [plan-staging-prod-github-deploy.md](./plan-staging-prod-github-deploy.md) (implementation checklist), [staging-setup.md](./staging-setup.md) (server details).

---

## 1. Principles

| Principle | Detail |
|-----------|--------|
| **One physical server** | Staging and prod processes both run here; isolated by **paths**, **ports**, **DBs**, **env files**. |
| **Flat layout** | Each environment has `repo/`, `api/`, `web/`, `env/`, `logs/` at the same depth — no nested `app/`. |
| **Two Git checkouts** | Staging `repo/` tracks **`main`**. Prod `repo/` checks out a **semver tag** (e.g. `v1.2.0`) for promotion-based deploy. |
| **Two databases** | One PostgreSQL instance; **`tttc_staging`** vs **`tttc_prod`** (separate users/passwords). |

---

## 2. URLs and upstream ports

| Public URL | Environment | Upstream (localhost) |
|------------|-------------|----------------------|
| `https://staging-app.treptower-teufel.de/` | Staging web | `127.0.0.1:5173` |
| `https://staging-api.treptower-teufel.de/` | Staging API | `127.0.0.1:8000` |
| `https://app.treptower-teufel.de/` | Prod web | `127.0.0.1:5174` |
| `https://api.treptower-teufel.de/` | Prod API | `127.0.0.1:8001` |

Caddy terminates TLS and reverse-proxies to these ports. **Staging and prod use different ports** so both stacks can run at once.

---

## 3. Directory tree

```text
/srv/tttc/
├── staging/
│   ├── repo/          ← git clone; branch main
│   ├── api/           ← synced from repo/api + .venv
│   ├── web/           ← built frontend
│   ├── env/           ← api.env, web.env (not in Git)
│   └── logs/
└── prod/
    ├── repo/          ← git clone; detached at tag vX.Y.Z
    ├── api/
    ├── web/
    ├── env/
    └── logs/
```

---

## 4. Path reference

### Staging

| Path | Purpose |
|------|---------|
| `/srv/tttc/staging/repo` | Clone of `https://github.com/Redundando/treptower-teufel-app.git`; deploy = `git pull origin main`. |
| `/srv/tttc/staging/api` | FastAPI + `.venv`; `WorkingDirectory` for staging API process. |
| `/srv/tttc/staging/web` | Frontend after `npm run build`; Vite preview or static serve. |
| `/srv/tttc/staging/env` | `api.env` (`DATABASE_URL` → `tttc_staging`, …). |
| `/srv/tttc/staging/logs` | Optional file logs. |

### Prod

| Path | Purpose |
|------|---------|
| `/srv/tttc/prod/repo` | Same remote; checkout **tag** on deploy (promote what ran on staging). |
| `/srv/tttc/prod/api` | FastAPI + `.venv`. |
| `/srv/tttc/prod/web` | Built frontend. |
| `/srv/tttc/prod/env` | `api.env` (`DATABASE_URL` → `tttc_prod`, **different** secrets from staging). |
| `/srv/tttc/prod/logs` | Optional file logs. |

---

## 5. PostgreSQL

| Database | DB user (example) | Used by |
|----------|-------------------|---------|
| `tttc_staging` | `tttc_staging_user` | `/srv/tttc/staging/env/api.env` |
| `tttc_prod` | `tttc_prod_user` | `/srv/tttc/prod/env/api.env` |

Create prod DB/user when prod stack is provisioned (see plan doc). Passwords only in env files / secrets store.

---

## 6. systemd unit names (target)

| Unit | Binds to |
|------|----------|
| `tttc-api-staging.service` | `/srv/tttc/staging/api`, port **8000**, `EnvironmentFile=/srv/tttc/staging/env/api.env` |
| `tttc-web-staging.service` | `/srv/tttc/staging/web`, port **5173** |
| `tttc-api-prod.service` | `/srv/tttc/prod/api`, port **8001**, `EnvironmentFile=/srv/tttc/prod/env/api.env` |
| `tttc-web-prod.service` | `/srv/tttc/prod/web`, port **5174** |

Unit file templates should live under **`ops/systemd/`** in the repo (update from legacy `tttc-api.service` / `tttc-web.service` during migration).

---

## 7. Caddy

Single config file: **`/etc/caddy/Caddyfile`**.

- **Four** `site` blocks: `staging-app`, `staging-api`, `app`, `api` (full hostnames as in §2).
- Staging app site: same pattern as today — e.g. `/api/*` → API, rest → web (see [caddy-staging.md](./caddy-staging.md)); extend for prod hosts and ports **5174** / **8001**.

---

## 8. Legacy path (migration)

Older docs and units used:

```text
/srv/tttc/app/{repo,api,web,env,logs}
```

That layout is **equivalent to staging only**, flattened under `app/` instead of `staging/`. **Target state** is `/srv/tttc/staging/...` as above. Move or re-clone per [plan-staging-prod-github-deploy.md](./plan-staging-prod-github-deploy.md).

---

*Update this file if paths, ports, or hostnames change.*
