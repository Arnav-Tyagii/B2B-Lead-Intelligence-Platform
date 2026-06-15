"""Enrichment orchestration with graceful degradation.

Single entry point `enrich_company()` that tries Gemini first and falls back to
the deterministic heuristic enricher whenever Gemini is unavailable (no key,
rate-limited, disabled, malformed output). The caller never has to know which
path produced the result — `Enrichment.source` records it.

The Gemini prompt asks for strict minified JSON with exactly the enrichment
fields, and we parse defensively + cap array/string lengths to control tokens,
latency, and document size.
"""

from app.core.logging import get_logger
from app.models.company import Company
from app.models.enrichment import Enrichment, EnrichmentSource
from app.services import gemini_client
from app.services.fallback_enricher import fallback_enrich

logger = get_logger(__name__)

# Caps mirror the fallback enricher so both sources yield comparable records.
_MAX_TECH = 6
_MAX_SIGNALS = 5
_MAX_TOPICS = 5
_MAX_PAINS = 4
_MAX_EMAIL_CHARS = 1200
_MAX_REC_CHARS = 600


def _build_prompt(company: Company) -> str:
    news = "; ".join(company.recent_news) or "none"
    # Explicit JSON contract + caps keep the response small and parseable.
    return (
        "You are a B2B go-to-market analyst. Given the company below, infer "
        "account intelligence and respond with STRICT MINIFIED JSON only — no "
        "prose, no code fences. Use exactly these keys:\n"
        '{"technographics":[str],"intent_signals":[str],"intent_topics":[str],'
        '"pain_points":[str],"outreach_email":str,"gtm_recommendation":str}\n'
        f"Limits: technographics<= {_MAX_TECH}, intent_signals<= {_MAX_SIGNALS}, "
        f"intent_topics<= {_MAX_TOPICS}, pain_points<= {_MAX_PAINS}, "
        f"outreach_email<= 120 words, gtm_recommendation<= 60 words.\n\n"
        f"Company: {company.name}\n"
        f"Domain: {company.domain}\n"
        f"Industry: {company.industry}\n"
        f"Employees: {company.employee_count}\n"
        f"Estimated revenue (USD): {company.estimated_revenue_usd}\n"
        f"HQ: {company.hq_location}, {company.country}\n"
        f"Description: {company.description}\n"
        f"Recent news: {news}\n"
    )


def _as_str_list(value: object, cap: int) -> list[str]:
    """Coerce arbitrary model output into a clean, capped list of strings."""
    if not isinstance(value, list):
        return []
    out = [str(v).strip() for v in value if str(v).strip()]
    return out[:cap]


def _parse_enrichment(data: dict) -> Enrichment:
    return Enrichment(
        technographics=_as_str_list(data.get("technographics"), _MAX_TECH),
        intent_signals=_as_str_list(data.get("intent_signals"), _MAX_SIGNALS),
        intent_topics=_as_str_list(data.get("intent_topics"), _MAX_TOPICS),
        pain_points=_as_str_list(data.get("pain_points"), _MAX_PAINS),
        outreach_email=str(data.get("outreach_email", "")).strip()[:_MAX_EMAIL_CHARS],
        gtm_recommendation=str(data.get("gtm_recommendation", "")).strip()[:_MAX_REC_CHARS],
        source=EnrichmentSource.GEMINI,
    )


async def enrich_company(company: Company) -> Enrichment:
    """Enrich one account, preferring Gemini and degrading to the fallback.

    Never raises: any Gemini problem results in a fallback enrichment so the
    pipeline (seed or live) always produces a usable record."""
    try:
        data = await gemini_client.generate_json(_build_prompt(company))
        enrichment = _parse_enrichment(data)
        # A response with no useful content is treated as a miss → fallback.
        if not enrichment.technographics and not enrichment.intent_signals:
            logger.info("Gemini returned empty enrichment for %s — using fallback", company.domain)
            return fallback_enrich(company)
        return enrichment
    except gemini_client.GeminiUnavailable as exc:
        logger.info("Falling back for %s: %s", company.domain, exc)
        return fallback_enrich(company)
