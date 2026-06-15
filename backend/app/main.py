"""FastAPI application entrypoint.

Wires together config, logging, the pooled Mongo client, startup index creation,
CORS, and the routers. Business logic lives in services — this file only
assembles the app (clean layering: api → services → repositories → models).

Run locally:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import accounts, enrich, health, icp, stats
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.indexes import ensure_indexes
from app.db.mongo import close_client, get_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    configure_logging()
    settings = get_settings()
    logger.info("Starting up (environment=%s)", settings.environment)
    # Ensure indexes once on boot so server-side filter/sort stays fast on M0.
    # Wrapped so a transient Atlas hiccup on a cold start doesn't crash boot.
    try:
        await ensure_indexes(get_db())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not ensure indexes on startup: %s", exc)

    yield

    # ── Shutdown ──
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="B2B Lead Intelligence Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS locked to the configured frontend origin(s).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(accounts.router)
    app.include_router(enrich.router)
    app.include_router(stats.router)
    app.include_router(icp.router)

    # Last-resort handler so an unexpected error returns clean JSON (and is
    # logged once) instead of leaking a stack trace to the client.
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
