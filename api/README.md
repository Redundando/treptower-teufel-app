# TTTC API (Backend)

FastAPI backend for the Treptower Teufel Club App. Runs against the `.env` in the **project root** (parent of `api/`).

## Setup (once)

From the **project root**:

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Or from anywhere with the repo path:

```powershell
cd "c:\dev\treptower teufel app api\api"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Ensure the root `.env` contains `DATABASE_URL=postgresql://tttc_dev_user:YOUR_PASSWORD@localhost:5432/tttc_dev`. If `/db` returns "password authentication failed", the password in `.env` must match the one you set for `tttc_dev_user` in PostgreSQL.

## Run (local dev)

From **project root** (so `.env` is found):

```powershell
cd "c:\dev\treptower teufel app api"
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
- **Docs:** http://127.0.0.1:8000/docs  

If you get `WinError 10013` (port in use or blocked), run on another port:  
`api\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir api --port 8001`  
