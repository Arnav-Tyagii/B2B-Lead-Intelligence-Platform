"""Single pooled Mongo client.

Atlas M0 (free tier) allows very few concurrent connections, so we create ONE
module-level Motor client and reuse it for the whole process. Motor's client is
itself an async connection pool — creating a client per request would exhaust
the free-tier connection limit. The client is created lazily and closed on
shutdown via the FastAPI lifespan.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level singleton. Do NOT instantiate AsyncIOMotorClient anywhere else.
_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        # maxPoolSize kept small to respect M0 connection limits.
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        logger.info("Created Mongo client (db=%s)", settings.mongodb_db_name)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """The application database. Repositories depend on this."""
    return get_client()[get_settings().mongodb_db_name]


async def ping() -> bool:
    """Liveness probe used by /health. Returns False instead of raising so the
    health endpoint can report degraded status without 500-ing."""
    try:
        await get_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001 - health check must never raise
        logger.warning("Mongo ping failed: %s", exc)
        return False


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("Closed Mongo client")
