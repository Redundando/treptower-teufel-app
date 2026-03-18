# Local development setup

**One place for “how do I run this project on my machine”.**  
Env strategy is in [env-and-secrets.md](./env-and-secrets.md); this doc is the step-by-step to get coding.

---

## 1. Prerequisites

| Software | Purpose | Notes |
|----------|---------|--------|
| **Git** | Clone repo, branches | — |
| **Python 3.12+** | Backend (FastAPI) | From [python.org](https://www.python.org/downloads/) or Chocolatey. |
| **PostgreSQL** | Local database | From [postgresql.org](https://www.postgresql.org/download/windows/). Add `bin` to PATH (e.g. `C:\Program Files\PostgreSQL\18\bin`). |
| **Node.js** | Frontend (Vite + Svelte) | From [nodejs.org](https://nodejs.org/) or Chocolatey. |

---

## 2. Clone the repo

```powershell
git clone https://github.com/Redundando/treptower-teufel-app.git
cd treptower-teufel-app
```

(Or use your existing clone path.)

---

## 3. Local PostgreSQL: database and user

Create a dedicated DB and user for local dev (do this once).

**1. Create the user** (replace `your_password` with a password you choose):

```powershell
psql -U postgres -h localhost -p 5432 -c "CREATE USER tttc_dev_user WITH ENCRYPTED PASSWORD 'your_password';"
```

**2. Create the database** (separate command; PostgreSQL does not allow `CREATE DATABASE` in the same transaction as `CREATE USER`):

```powershell
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE tttc_dev OWNER tttc_dev_user;"
```

You’ll be prompted for the `postgres` user password each time. Use the same `your_password` in your `.env` in the next step.

---

## 4. Environment file

- Copy the example env file and add your real values:
  ```powershell
  copy .env.example .env
  ```
- Edit **`.env`** and set at least:
  ```env
  DATABASE_URL=postgresql://tttc_dev_user:your_password@localhost:5432/tttc_dev
  ```
- **Do not commit** `.env`. It is gitignored.

See [env-and-secrets.md](./env-and-secrets.md) for the full env/secrets strategy (including optional `.env.staging`).

---

## 5. Run the API (backend)

**One-time setup** (venv + install):

From the **project root**:

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

**Start the server** — easiest from repo root:

```powershell
.\scripts\run-api.ps1
```

(Optional: `.\scripts\run-api.ps1 --port 8001` if port 8000 is busy.)

Or manually from project root (so `.env` is found):

```powershell
api\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir api
```

Or from inside `api/` with venv activated:

```powershell
cd api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

- **Health:** http://127.0.0.1:8000/health  
- **DB check:** http://127.0.0.1:8000/db  
- **API docs:** http://127.0.0.1:8000/docs  

More detail in [api/README.md](../api/README.md).  
If you run the API on another port (e.g. 8001), set the proxy target in `web/vite.config.ts` to match.

---

## 6. Run the frontend (web)

**One-time setup:**

```powershell
cd web
npm install
```

**Start the dev server:**

```powershell
cd web
npm run dev
```

- **App:** http://localhost:5173  
- The page shows “Hello, Treptower Teufel” and calls the API `/health` via a proxy. The API must be running on port 8000 (or change `web/vite.config.ts` proxy target to your port).

**Build for production:** `npm run build` → output in `web/dist/`.

---

## 7. Troubleshooting

| Issue | What to do |
|--------|------------|
| **`psql` not found** | Add PostgreSQL `bin` to your PATH (e.g. `C:\Program Files\PostgreSQL\18\bin`). Restart the terminal (or Cursor) so it picks up PATH. |
| **`WinError 10013`** when starting uvicorn | Port 8000 is in use or blocked. Use another port: `--port 8001` (and open http://127.0.0.1:8001/...). Or free 8000: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F`. |
| **`/db` returns “password authentication failed for user tttc_dev_user”** | The password in `.env` must match the one you set for `tttc_dev_user` in PostgreSQL. Fix either the DB password or `DATABASE_URL` in `.env`. |
| **`.env` not loaded** | Run uvicorn from the **project root** with `--app-dir api`, or run from inside `api/` (config looks for `.env` in the parent directory). |
| **Frontend shows “API: offline”** | Start the API first (port 8000, or update the proxy in `web/vite.config.ts`). |

---

## 8. Quick reference

| Task | Where |
|------|--------|
| Repo | https://github.com/Redundando/treptower-teufel-app |
| Env / secrets | [env-and-secrets.md](./env-and-secrets.md) |
| API run details | [api/README.md](../api/README.md) |
| Staging / deploy | [deploy.md](./deploy.md), [staging-setup.md](./staging-setup.md) |

---

*Update this doc when we add the frontend or change local requirements.*
