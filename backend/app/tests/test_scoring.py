"""Unit tests for the ICP scoring engine.

These pin down the transparent-scoring contract: correct totals, partial-credit
bands, tier thresholds, and per-dimension caps.
"""

from app.models.fit import Tier
from app.services.scoring import score_account
from app.tests.conftest import default_icp, make_company, make_enrichment

ICP = default_icp()


def test_perfect_account_is_hot_and_full_score():
    fit = score_account(make_company(), make_enrichment(), ICP)
    # Target industry + in-band size/revenue + target country + 3 tech + 3 signals
    # => every dimension maxed => 100.
    assert fit.total == 100
    assert fit.tier == Tier.HOT
    assert fit.breakdown.industry == 25
    assert fit.breakdown.company_size == 20
    assert fit.breakdown.revenue == 15
    assert fit.breakdown.geography == 10
    assert fit.breakdown.technographics == 15
    assert fit.breakdown.intent == 15


def test_cold_account_off_icp_everything():
    company = make_company(
        industry="Manufacturing",      # off-ICP
        employee_count=30,             # far below band
        estimated_revenue_usd=1_000_000,  # far below band
        country="Brazil",              # off-ICP
    )
    enrichment = make_enrichment(technographics=[], intent_signals=[])
    fit = score_account(company, enrichment, ICP)
    assert fit.total == 0
    assert fit.tier == Tier.COLD


def test_size_partial_credit_within_2x():
    # 150 employees: below 200 but >= 100 (200/2) => half of 20 = 10.
    company = make_company(employee_count=150)
    fit = score_account(company, make_enrichment(), ICP)
    assert fit.breakdown.company_size == 10

    # 9000 employees: above 5000 but <= 10000 => half = 10.
    company2 = make_company(employee_count=9000)
    fit2 = score_account(company2, make_enrichment(), ICP)
    assert fit2.breakdown.company_size == 10

    # 30 employees: below 100 => 0.
    company3 = make_company(employee_count=30)
    fit3 = score_account(company3, make_enrichment(), ICP)
    assert fit3.breakdown.company_size == 0


def test_revenue_partial_credit_within_2x():
    # $15M: below $20M but >= $10M => half of 15 = 7.5.
    company = make_company(estimated_revenue_usd=15_000_000)
    fit = score_account(company, make_enrichment(), ICP)
    assert fit.breakdown.revenue == 7.5


def test_technographics_scale_with_matches():
    one = make_enrichment(technographics=["Salesforce"])  # 1 of 3 needed
    fit = score_account(make_company(), one, ICP)
    # 15 * (1/3) = 5.0
    assert fit.breakdown.technographics == 5.0

    # Non-target tools earn nothing.
    none = make_enrichment(technographics=["Slack", "Zoom"])
    fit_none = score_account(make_company(), none, ICP)
    assert fit_none.breakdown.technographics == 0


def test_intent_scales_and_dedupes():
    # Duplicate signals collapse to one distinct => 15 * (1/3) = 5.0.
    dup = make_enrichment(intent_signals=["Hiring", "hiring", " HIRING "])
    fit = score_account(make_company(), dup, ICP)
    assert fit.breakdown.intent == 5.0


def test_tier_thresholds():
    # Build a Warm account: industry(25) + geography(10) + size(20) = 55 -> Warm.
    warm_company = make_company(estimated_revenue_usd=1_000_000)  # revenue out
    warm_enrich = make_enrichment(technographics=[], intent_signals=[])
    fit = score_account(warm_company, warm_enrich, ICP)
    assert fit.total == 55
    assert fit.tier == Tier.WARM


def test_breakdown_never_exceeds_weights():
    # Even with many tech/signals, dimensions cap at their weight.
    loaded = make_enrichment(
        technographics=["Salesforce", "HubSpot", "Snowflake", "Segment", "Gong", "Outreach"],
        intent_signals=["a", "b", "c", "d", "e"],
    )
    fit = score_account(make_company(), loaded, ICP)
    assert fit.breakdown.technographics == 15
    assert fit.breakdown.intent == 15
    assert fit.total <= 100


def test_rationale_is_populated():
    fit = score_account(make_company(), make_enrichment(), ICP)
    assert fit.rationale
    assert "target vertical" in fit.rationale
