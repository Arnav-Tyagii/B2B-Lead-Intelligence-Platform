"""Firmographic data for a company — the raw input to enrichment + scoring."""

from pydantic import BaseModel, Field


class Company(BaseModel):
    name: str
    domain: str = Field(description="Canonical domain; also used as the account _id.")
    industry: str
    employee_count: int = Field(ge=0)
    estimated_revenue_usd: int = Field(ge=0, description="Estimated annual revenue in USD.")
    hq_location: str = Field(description="Human-readable HQ, e.g. 'San Francisco, CA'.")
    country: str
    founded_year: int | None = None
    description: str = ""
    # 1-2 short headlines per company; the fallback enricher mines these for
    # intent signals (funding / hiring / launch keywords).
    recent_news: list[str] = Field(default_factory=list)
