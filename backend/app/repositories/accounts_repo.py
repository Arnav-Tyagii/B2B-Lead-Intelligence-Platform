"""Repository for the `accounts` collection — the ONLY place that touches Mongo
for accounts. Routers/services never run queries directly (clean layering).

Documents use the company domain as `_id`, so writes/reads go through the
Account model's `_id`/`domain` alias. Enums are serialized with mode="json" so
they persist as plain strings (BSON-friendly and easy to query/index).

All filtering/sorting/pagination is pushed DOWN to Mongo (server-side) using the
indexes created on startup — we never load the whole collection into memory.
"""

from app.db.indexes import ACCOUNTS_COLLECTION
from app.db.mongo import get_db
from app.models.account import Account
from app.models.api import AccountsQuery, SortOrder


def _collection():
    return get_db()[ACCOUNTS_COLLECTION]


def _build_filter(q: AccountsQuery) -> dict:
    """Translate query params into a Mongo filter. Each clause maps to an
    indexed field so the query stays a fast index scan on M0."""
    f: dict = {}
    if q.tier is not None:
        f["fit.tier"] = q.tier.value
    if q.industry:
        f["company.industry"] = q.industry
    if q.country:
        f["company.country"] = q.country
    if q.min_score is not None:
        f["fit.total"] = {"$gte": q.min_score}
    if q.source is not None:
        f["enrichment.source"] = q.source.value
    if q.data_source:
        f["company.data_source"] = q.data_source
    return f


async def find_paginated(q: AccountsQuery) -> tuple[list[Account], int]:
    """Server-side filter + sort + paginate. Returns (page_items, total_matching).

    `total` is computed with the same filter so the frontend can render accurate
    page counts without ever fetching the full result set."""
    col = _collection()
    filt = _build_filter(q)

    total = await col.count_documents(filt)

    # Build the sort spec. For AI_FIRST we sort by source descending first:
    # "gemini" > "fallback" lexicographically, so descending puts the genuinely
    # AI-enriched accounts ahead, then ranks each group by score.
    if q.sort == SortOrder.AI_FIRST:
        sort_spec = [("enrichment.source", -1), ("fit.total", -1)]
    elif q.sort == SortOrder.REAL_FIRST:
        # is_real_data is a persisted bool: descending puts True (real) ahead of
        # False (synthetic) and missing (legacy docs) last — a null-safe ordering.
        sort_spec = [("company.is_real_data", -1), ("fit.total", -1)]
    elif q.sort == SortOrder.SCORE_ASC:
        sort_spec = [("fit.total", 1)]
    else:  # SCORE_DESC
        sort_spec = [("fit.total", -1)]

    cursor = (
        col.find(filt)
        .sort(sort_spec)
        .skip((q.page - 1) * q.page_size)
        .limit(q.page_size)
    )
    items = [Account(**doc) async for doc in cursor]
    return items, total


async def get_by_domain(domain: str) -> Account | None:
    doc = await _collection().find_one({"_id": domain})
    return Account(**doc) if doc else None


async def delete_all() -> int:
    """Empty the collection. Destructive — only called from the seed's --reset."""
    result = await _collection().delete_many({})
    return result.deleted_count


async def delete_synthetic() -> int:
    """Delete non-real accounts: synthetic plus any legacy docs predating the
    is_real_data field (matched via $ne True, which also catches missing)."""
    result = await _collection().delete_many({"company.is_real_data": {"$ne": True}})
    return result.deleted_count


async def upsert_account(account: Account) -> None:
    """Insert or replace an account by domain (_id). Idempotent — re-seeding /
    re-enriching overwrites cleanly rather than duplicating."""
    doc = account.model_dump(by_alias=True, mode="json")
    await _collection().replace_one({"_id": account.domain}, doc, upsert=True)


# ── Aggregations for /stats and the seed report ──

async def count() -> int:
    return await _collection().count_documents({})


async def tier_counts() -> dict[str, int]:
    pipeline = [{"$group": {"_id": "$fit.tier", "count": {"$sum": 1}}}]
    result: dict[str, int] = {}
    async for row in _collection().aggregate(pipeline):
        result[row["_id"]] = row["count"]
    return result


async def industry_counts() -> list[tuple[str, int]]:
    """(industry, count) sorted by count desc — for the top-industries chart."""
    pipeline = [
        {"$group": {"_id": "$company.industry", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    return [(row["_id"], row["count"]) async for row in _collection().aggregate(pipeline)]


async def average_score() -> float:
    pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$fit.total"}}}]
    async for row in _collection().aggregate(pipeline):
        return round(row["avg"], 1)
    return 0.0
