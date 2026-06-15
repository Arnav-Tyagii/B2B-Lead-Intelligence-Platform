"""Accounts routers — thin. All logic lives in accounts_service.

GET /accounts paginates, filters, and sorts SERVER-SIDE (the collection is never
returned whole). Query params are validated by FastAPI and assembled into the
AccountsQuery model.
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.account import Account
from app.models.api import AccountsQuery, PaginatedAccounts, SortOrder
from app.models.enrichment import EnrichmentSource
from app.models.fit import Tier
from app.services import accounts_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


# response_model_by_alias=False so the domain field serializes as "domain"
# (not its Mongo "_id" alias) — a cleaner contract for the frontend types.
@router.get("", response_model=PaginatedAccounts, response_model_by_alias=False)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, description="Max 100 (free-tier guard)."),
    tier: Tier | None = Query(None),
    industry: str | None = Query(None),
    country: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=100),
    source: EnrichmentSource | None = Query(None),
    sort: SortOrder = Query(SortOrder.SCORE_DESC),
) -> PaginatedAccounts:
    query = AccountsQuery(
        page=page,
        page_size=page_size,
        tier=tier,
        industry=industry,
        country=country,
        min_score=min_score,
        source=source,
        sort=sort,
    )
    return await accounts_service.list_accounts(query)


@router.get("/{domain}", response_model=Account, response_model_by_alias=False)
async def get_account(domain: str) -> Account:
    account = await accounts_service.get_account(domain)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{domain}' not found")
    return account
