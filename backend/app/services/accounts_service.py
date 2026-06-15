"""Account business logic: list (cached), fetch, and on-demand enrich+score.

Routers stay thin and delegate here. This module owns the read cache for the
list endpoint and the cache-invalidation that must happen after a write.
"""

import math

from app.core.cache import TTLCache
from app.core.logging import get_logger
from app.models.account import Account
from app.models.api import AccountsQuery, EnrichRequest, PaginatedAccounts
from app.models.company import Company
from app.repositories import accounts_repo, icp_repo
from app.services import stats_service
from app.services.enrichment import enrich_company
from app.services.scoring import score_account

logger = get_logger(__name__)

# Short TTL: list views change rarely between clicks but we still want fresh data
# soon after an enrich. 15s comfortably absorbs dashboard browsing bursts.
_list_cache = TTLCache(ttl_seconds=15)


def _invalidate_read_caches() -> None:
    """After any write, drop cached list pages and stats so the next read is
    fresh. Cheap because the caches are per-process and small."""
    _list_cache.clear()
    stats_service.invalidate()


async def list_accounts(q: AccountsQuery) -> PaginatedAccounts:
    cache_key = q.model_dump_json()  # stable key across identical queries
    cached = _list_cache.get(cache_key)
    if cached is not None:
        return cached

    items, total = await accounts_repo.find_paginated(q)
    total_pages = math.ceil(total / q.page_size) if total else 0
    result = PaginatedAccounts(
        items=items,
        total=total,
        page=q.page,
        page_size=q.page_size,
        total_pages=total_pages,
    )
    _list_cache.set(cache_key, result)
    return result


async def get_account(domain: str) -> Account | None:
    return await accounts_repo.get_by_domain(domain)


def _company_from_request(req: EnrichRequest) -> Company:
    """Build a Company from a sparse live-enrich request, filling sensible
    defaults so scoring always has values to work with. A user can submit just a
    domain and still get a usable result ('Stop the Press')."""
    # Derive a display name from the domain if none provided (e.g. acme.com -> Acme).
    fallback_name = req.domain.split(".")[0].replace("-", " ").title()
    return Company(
        name=req.name or fallback_name,
        domain=req.domain.strip().lower(),
        industry=req.industry or "SaaS",
        employee_count=req.employee_count if req.employee_count is not None else 500,
        estimated_revenue_usd=(
            req.estimated_revenue_usd if req.estimated_revenue_usd is not None else 50_000_000
        ),
        hq_location=req.hq_location or "Unknown",
        country=req.country or "United States",
        founded_year=req.founded_year,
        description=req.description or "",
        recent_news=req.recent_news,
    )


async def enrich_and_store(req: EnrichRequest) -> Account:
    """On-demand: enrich ONE account (single Gemini call, graceful fallback),
    score it against the current ICP, persist, and return it."""
    company = _company_from_request(req)
    enrichment = await enrich_company(company)  # one live call; falls back if needed
    icp = await icp_repo.get_icp()
    fit = score_account(company, enrichment, icp)
    account = Account(
        _id=company.domain, company=company, enrichment=enrichment, fit=fit
    )
    await accounts_repo.upsert_account(account)
    _invalidate_read_caches()  # the new/updated account must show up in reads
    logger.info("Live-enriched %s (source=%s, tier=%s)",
                company.domain, enrichment.source.value, fit.tier.value)
    return account
