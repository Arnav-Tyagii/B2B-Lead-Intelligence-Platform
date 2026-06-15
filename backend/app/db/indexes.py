"""Index creation, run once on startup.

The accounts endpoint paginates/filters/sorts server-side, so the fields it
filters and sorts on MUST be indexed or M0 will do slow collection scans.
`create_index` is idempotent — calling it on every startup is safe and cheap
(Mongo no-ops if the index already exists).

Note: `_id` (= company domain) is unique and indexed by Mongo automatically,
so we don't add an index for domain lookups.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger

logger = get_logger(__name__)

ACCOUNTS_COLLECTION = "accounts"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    accounts = db[ACCOUNTS_COLLECTION]

    # Filter fields.
    await accounts.create_index("fit.tier")
    await accounts.create_index("company.industry")
    await accounts.create_index("company.country")
    await accounts.create_index("enrichment.source")
    # Sort/range field — descending is the common "best accounts first" sort.
    await accounts.create_index([("fit.total", -1)])

    logger.info("Ensured indexes on '%s'", ACCOUNTS_COLLECTION)
