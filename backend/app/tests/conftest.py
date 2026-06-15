"""Shared test fixtures/builders for the domain-service tests."""

from app.models.company import Company
from app.models.enrichment import Enrichment, EnrichmentSource
from app.models.icp import ICP


def make_company(**overrides) -> Company:
    """A Company that is a strong ICP fit by default; override per test."""
    defaults = dict(
        name="Acme",
        domain="acme.com",
        industry="SaaS",                       # target vertical
        employee_count=500,                    # inside 200-5000
        estimated_revenue_usd=50_000_000,      # inside 20M-2B
        hq_location="San Francisco, CA",
        country="United States",               # target market
        founded_year=2015,
        description="A SaaS company.",
        recent_news=[],
    )
    defaults.update(overrides)
    return Company(**defaults)


def make_enrichment(**overrides) -> Enrichment:
    defaults = dict(
        technographics=["Salesforce", "HubSpot", "Snowflake"],  # 3 ICP matches
        intent_signals=["Raised funding", "Hiring SDRs", "Launched product"],  # 3 signals
        intent_topics=["Funding", "Hiring", "Launch"],
        pain_points=["Slow lead routing"],
        outreach_email="Hi team...",
        gtm_recommendation="Prioritize.",
        source=EnrichmentSource.FALLBACK,
    )
    defaults.update(overrides)
    return Enrichment(**defaults)


def default_icp() -> ICP:
    return ICP()
