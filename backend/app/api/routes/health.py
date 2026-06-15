"""Liveness endpoint.

Doubles as the keep-warm target: a free cron pinger hits /health to stop
Render's free web service from sleeping, and the frontend warms the backend on
first load. It reports DB connectivity but stays 200 even if Mongo is briefly
unreachable, so a cold start / transient blip doesn't look like an outage to the
pinger — the `database` field carries the real status.
"""

from fastapi import APIRouter

from app.db.mongo import ping

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    db_ok = await ping()
    return {
        "status": "ok",
        "database": "connected" if db_ok else "unreachable",
    }
