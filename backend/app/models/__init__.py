"""Pydantic v2 schemas — the single source of truth for the API contract.

Re-exported here so callers can `from app.models import Account, Company, ...`.
The matching TypeScript types live in `frontend/src/lib/types.ts`.
"""

from app.models.account import Account
from app.models.company import Company
from app.models.enrichment import Enrichment, EnrichmentSource
from app.models.fit import Fit, FitBreakdown, Tier
from app.models.icp import ICP
from app.models.api import (
    AccountsQuery,
    EnrichRequest,
    PaginatedAccounts,
    SortOrder,
    Stats,
)

__all__ = [
    "Account",
    "Company",
    "Enrichment",
    "EnrichmentSource",
    "Fit",
    "FitBreakdown",
    "Tier",
    "ICP",
    "AccountsQuery",
    "EnrichRequest",
    "PaginatedAccounts",
    "SortOrder",
    "Stats",
]
