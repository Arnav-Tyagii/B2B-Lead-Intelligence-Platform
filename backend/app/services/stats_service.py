"""Dashboard stats, assembled from repository aggregations and cached.

The dashboard hits this on every load, so we cache the assembled Stats for a
short window. `invalidate()` is called after writes (see accounts_service).
"""

from app.core.cache import TTLCache
from app.models.api import IndustryCount, Stats, TierCount
from app.models.fit import Tier
from app.repositories import accounts_repo

_CACHE_KEY = "stats"
_cache = TTLCache(ttl_seconds=30)


def invalidate() -> None:
    _cache.clear()


async def get_stats() -> Stats:
    cached = _cache.get(_CACHE_KEY)
    if cached is not None:
        return cached

    total = await accounts_repo.count()
    tiers = await accounts_repo.tier_counts()
    industries = await accounts_repo.industry_counts()
    avg = await accounts_repo.average_score()

    # Always emit all three tiers (0 when absent) so the chart is stable.
    tier_distribution = [
        TierCount(tier=t, count=tiers.get(t.value, 0)) for t in Tier
    ]
    industry_distribution = [
        IndustryCount(industry=name, count=cnt) for name, cnt in industries
    ]

    stats = Stats(
        total_accounts=total,
        hot_count=tiers.get(Tier.HOT.value, 0),
        average_score=avg,
        tier_distribution=tier_distribution,
        industry_distribution=industry_distribution,
    )
    _cache.set(_CACHE_KEY, stats)
    return stats
