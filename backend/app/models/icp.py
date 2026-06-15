"""Ideal Customer Profile configuration.

Defaults encode the ICP from the build spec. The ICP is persisted in Mongo so it
can be edited (PUT /icp) and the book re-scored, but these defaults are the
source of truth when no document exists yet. Weights must sum to 100; the
scoring engine relies on that invariant.
"""

from pydantic import BaseModel, Field, model_validator


class ICPWeights(BaseModel):
    industry: int = 25
    company_size: int = 20
    revenue: int = 15
    geography: int = 10
    technographics: int = 15
    intent: int = 15

    @model_validator(mode="after")
    def _must_sum_to_100(self) -> "ICPWeights":
        total = (
            self.industry
            + self.company_size
            + self.revenue
            + self.geography
            + self.technographics
            + self.intent
        )
        if total != 100:
            raise ValueError(f"ICP weights must sum to 100 (got {total}).")
        return self


class ICP(BaseModel):
    target_industries: list[str] = Field(
        default_factory=lambda: [
            "SaaS",
            "FinTech",
            "Cybersecurity",
            "MarTech",
            "Cloud Infrastructure",
            "E-commerce",
            "HR Tech",
            "Data & Analytics",
        ]
    )
    # Employee band: full points inside, half points within 2x (see scoring engine).
    employee_min: int = 200
    employee_max: int = 5000
    # Revenue band (USD), same partial-credit rule.
    revenue_min_usd: int = 20_000_000
    revenue_max_usd: int = 2_000_000_000
    target_countries: list[str] = Field(
        default_factory=lambda: [
            "United States",
            "United Kingdom",
            "Canada",
            "India",
            "Germany",
        ]
    )
    target_technographics: list[str] = Field(
        default_factory=lambda: [
            "Salesforce",
            "HubSpot",
            "Marketo",
            "Snowflake",
            "Segment",
            "Outreach",
            "Salesloft",
            "Gong",
            "6sense",
            "Clearbit",
        ]
    )
    weights: ICPWeights = Field(default_factory=ICPWeights)
