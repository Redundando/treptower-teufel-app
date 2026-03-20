"""TTTC API — FastAPI application."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import CONFIG
from app.auth.router import router as auth_router
from app.members.router import router as members_router

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
app.include_router(members_router)
