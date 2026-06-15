"""ICP fit score for an account.

The score is intentionally transparent: every account carries the per-dimension
`breakdown` and a human-readable `rationale` so the UI can explain *why* an
account scored the way it did (a core product requirement).
"""

from enum import Enum

from pydantic import BaseModel, Field


class Tier(str, Enum):
    HOT = "Hot"
    WARM = "Warm"
    COLD = "Cold"


class FitBreakdown(BaseModel):
    """Points earned per dimension. Each is capped at that dimension's weight
    (industry 25, company_size 20, revenue 15, geography 10,
    technographics 15, intent 15 — summing to 100)."""

    industry: float = Field(ge=0)
    company_size: float = Field(ge=0)
    revenue: float = Field(ge=0)
    geography: float = Field(ge=0)
    technographics: float = Field(ge=0)
    intent: float = Field(ge=0)


class Fit(BaseModel):
    total: float = Field(ge=0, le=100)
    tier: Tier
    breakdown: FitBreakdown
    rationale: str = ""
