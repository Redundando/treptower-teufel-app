"""TTTC API — FastAPI application."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Depends
from streamator.emitter import JobEmitter
from streamator.fastapi import make_job_stream_response

from app.config import CONFIG
from app.auth.router import router as auth_router
from app.netxp_members.router import router as netxp_members_router
from app.netxp_members.public_stats import router as netxp_public_stats_router
from app.auth.deps import AuthenticatedUser, require_admin

app = FastAPI(
    title="TTTC API",
    description="Treptower Teufel Club App — Member & Admin API",
    version="0.1.0",
)


@app.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


@app.get("/db")
async def db_check():
    """Check database connectivity. Returns 503 if DATABASE_URL missing or connection fails."""
    database_url = CONFIG["app"]["database"]["url"]
    if not database_url or not database_url.strip():
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "DATABASE_URL not set"},
        )
    try:
        import asyncpg
        conn = await asyncpg.connect(database_url)
        try:
            row = await conn.fetchrow("SELECT 1 AS n")
            return {"status": "ok", "db": "connected", "check": row["n"]}
        finally:
            await conn.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )


app.include_router(auth_router)
app.include_router(netxp_members_router)
app.include_router(netxp_public_stats_router)


@app.get("/job/{job_id}/stream")
async def job_stream(job_id: str, _: AuthenticatedUser = Depends(require_admin)):
    # streamator's stream endpoint is auth-agnostic by default; we protect it here.
    return make_job_stream_response(job_id)


@app.get("/job/{job_id}/result")
async def job_result(job_id: str, _: AuthenticatedUser = Depends(require_admin)):
    data = JobEmitter.pop_result(job_id)
    if data is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return data


@app.post("/job/{job_id}/cancel")
async def job_cancel(job_id: str, _: AuthenticatedUser = Depends(require_admin)):
    JobEmitter.cancel(job_id)
    return {"cancelled": job_id}
