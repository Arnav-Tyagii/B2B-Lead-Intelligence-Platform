"""Liveness endpoint.

Doubles as the keep-warm target: a free uptime pinger (e.g. UptimeRobot) hits
/health to stop Render's free web service from sleeping, and the frontend warms
the backend on first load.

Both GET and HEAD are handled explicitly:
  - GET  reports DB connectivity (used by the frontend + humans). It stays 200
         even if Mongo is briefly unreachable, so a cold start / transient blip
         doesn't look like an outage — the `database` field carries the truth.
  - HEAD is what uptime monitors use by default. It returns a fast 200 with no
         body and skips the Mongo round-trip, so frequent keep-warm pings stay
         cheap and never touch the M0 connection budget.
"""

from fastapi import APIRouter, Request, Response

from app.db.mongo import ping

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"])
async def health(request: Request):
    if request.method == "HEAD":
        # Monitors only need a 200 to confirm the service is awake.
        return Response(status_code=200)

    db_ok = await ping()
    return {
        "status": "ok",
        "database": "connected" if db_ok else "unreachable",
    }
