"""Request/response DTOs for the API layer.

These shape what crosses the wire (and are mirrored in the frontend's
types.ts). Keeping them separate from the domain models lets the API evolve
(pagination envelopes, query params) without touching the stored schema.
"""

from enum import Enum

from pydantic import BaseModel, Field

from app.models.account import Account
from app.models.enrichment import EnrichmentSource
from app.models.fit import Tier


class SortOrder(str, Enum):
    SCORE_DESC = "score_desc"
    SCORE_ASC = "score_asc"
    # AI-enriched accounts first, then by score — surfaces genuinely
    # Gemini-enriched records at the top of the book.
    AI_FIRST = "ai_first"
    # Real (e.g. SEC-sourced) firmographics first, then by score — surfaces
    # genuinely acquired accounts above the synthetic book.
    REAL_FIRST = "real_first"


class AccountsQuery(BaseModel):
    """Validated query params for GET /accounts. Bounds enforce the free-tier
    rule that we never return the whole collection."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    tier: Tier | None = None
    industry: str | None = None
    country: str | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)
    source: EnrichmentSource | None = None
    # Provenance filter, e.g. "sec_edgar" (real) or "synthetic".
    data_source: str | None = None
    sort: SortOrder = SortOrder.SCORE_DESC


class PaginatedAccounts(BaseModel):
    items: list[Account]
    total: int = Field(description="Total matching documents (pre-pagination).")
    page: int
    page_size: int
    total_pages: int


class TierCount(BaseModel):
    tier: Tier
    count: int


class IndustryCount(BaseModel):
    industry: str
    count: int


class Stats(BaseModel):
    total_accounts: int
    hot_count: int
    average_score: float
    tier_distribution: list[TierCount]
    industry_distribution: list[IndustryCount]


class EnrichRequest(BaseModel):
    """Body for POST /enrich — a minimal company profile to enrich on demand.

    Most fields are optional so a user can submit just a domain; the service
    fills sensible defaults before enriching + scoring the single account."""

    domain: str
    name: str | None = None
    industry: str | None = None
    employee_count: int | None = Field(default=None, ge=0)
    estimated_revenue_usd: int | None = Field(default=None, ge=0)
    hq_location: str | None = None
    country: str | None = None
    founded_year: int | None = None
    description: str | None = None
    recent_news: list[str] = Field(default_factory=list)
