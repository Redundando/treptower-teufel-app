"""TTTC API — FastAPI application."""
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import DATABASE_URL

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
    if not DATABASE_URL or not DATABASE_URL.strip():
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "DATABASE_URL not set"},
        )
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
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
