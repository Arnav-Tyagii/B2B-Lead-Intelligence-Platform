"""Unit tests for the deterministic fallback enricher.

Pins down: determinism (domain-seeded), provenance, news-driven intent signals,
industry-driven technographics, populated outreach/recommendation, and caps.
"""

from app.models.enrichment import EnrichmentSource
from app.services.fallback_enricher import (
    _MAX_PAINS,
    _MAX_SIGNALS,
    _MAX_TECH,
    fallback_enrich,
)
from app.tests.conftest import make_company


def test_is_deterministic_per_domain():
    company = make_company(recent_news=["Acme raised a $20M Series B funding round."])
    a = fallback_enrich(company)
    b = fallback_enrich(company)
    assert a == b  # identical output for the same domain


def test_different_domains_differ():
    a = fallback_enrich(make_company(domain="acme.com"))
    b = fallback_enrich(make_company(domain="globex.io"))
    # Pain-point ordering is domain-seeded, so the two should not be identical.
    assert a.pain_points != b.pain_points or a.technographics != b.technographics


def test_source_is_fallback():
    assert fallback_enrich(make_company()).source == EnrichmentSource.FALLBACK


def test_intent_signals_mined_from_news():
    company = make_company(
        recent_news=[
            "Acme raised a $50M Series C funding round.",
            "Acme announces plans to hire 100 engineers this year.",
        ]
    )
    enrichment = fallback_enrich(company)
    joined = " ".join(enrichment.intent_signals).lower()
    assert "funding" in joined
    assert "hiring" in joined


def test_no_news_means_no_intent_signals():
    enrichment = fallback_enrich(make_company(recent_news=[]))
    assert enrichment.intent_signals == []


def test_technographics_reflect_industry():
    # SaaS stack includes Salesforce per the industry mapping.
    enrichment = fallback_enrich(make_company(industry="SaaS"))
    assert "Salesforce" in enrichment.technographics


def test_outreach_and_recommendation_populated():
    enrichment = fallback_enrich(make_company())
    assert enrichment.outreach_email.strip()
    assert enrichment.gtm_recommendation.strip()
    assert make_company().name in enrichment.outreach_email


def test_caps_respected():
    company = make_company(
        recent_news=[
            "raised funding round", "hiring engineers", "launches new product",
            "announces partnership", "acquires competitor", "international expansion",
        ]
    )
    enrichment = fallback_enrich(company)
    assert len(enrichment.technographics) <= _MAX_TECH
    assert len(enrichment.intent_signals) <= _MAX_SIGNALS
    assert len(enrichment.pain_points) <= _MAX_PAINS
