"""Deterministic, domain-seeded fallback enricher.

Used whenever Gemini is unavailable (no key, rate-limited, or disabled after a
fatal error). Two design goals:

1. **Deterministic** — seeded by the company domain so the same company always
   produces the same enrichment. That keeps the dashboard stable across runs and
   makes the output unit-testable.
2. **Plausible** — technographics inferred from industry, intent signals mined
   from `recent_news` keywords (funding / hiring / launch / ...), plus templated
   pain points, a personalized outreach email, and a GTM recommendation.

It never calls the network and never raises, so it is a safe last resort.
"""

import hashlib
import random

from app.models.company import Company
from app.models.enrichment import Enrichment, EnrichmentSource

# Output caps — keep documents lean (M0 is 512MB) and mirror the Gemini caps so
# both sources produce comparably sized records.
_MAX_TECH = 6
_MAX_SIGNALS = 5
_MAX_TOPICS = 5
_MAX_PAINS = 4

# Plausible stacks by industry. Values intentionally overlap the ICP target
# technographics so the scoring engine has something to reward.
_INDUSTRY_TECH: dict[str, list[str]] = {
    "SaaS": ["Salesforce", "HubSpot", "Segment", "Snowflake", "Outreach", "Gong"],
    "FinTech": ["Salesforce", "Snowflake", "Marketo", "6sense", "Clearbit"],
    "Cybersecurity": ["Salesforce", "Outreach", "Salesloft", "Snowflake", "6sense"],
    "MarTech": ["HubSpot", "Marketo", "Segment", "Clearbit", "Salesforce"],
    "Cloud Infrastructure": ["Snowflake", "Segment", "Salesforce", "Gong", "Outreach"],
    "E-commerce": ["HubSpot", "Segment", "Clearbit", "Salesforce", "Marketo"],
    "HR Tech": ["HubSpot", "Salesforce", "Marketo", "Salesloft", "Outreach"],
    "Data & Analytics": ["Snowflake", "Segment", "Salesforce", "6sense", "Gong"],
}
_DEFAULT_TECH = ["Salesforce", "HubSpot", "Google Workspace", "Slack", "Zoom"]

# news keyword -> the intent signal it implies. Order is significant only for
# readability; matches are de-duplicated.
_NEWS_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("funding", "raised", "series", "investment", "round"),
     "Recently raised funding — fresh budget for new tooling"),
    (("hiring", "hire", "hires", "headcount", "expands team", "recruiting"),
     "Active hiring — scaling the go-to-market team"),
    (("launch", "launches", "unveils", "new product", "introduces"),
     "Launched a new product — expansion motion underway"),
    (("partnership", "partners", "integration", "alliance"),
     "New partnership — ecosystem expansion"),
    (("acquire", "acquisition", "acquires", "merger"),
     "M&A activity — post-deal integration needs"),
    (("expansion", "opens office", "international", "global"),
     "Geographic expansion — new-market entry"),
]

_PAIN_POINTS: list[str] = [
    "Fragmented revenue data across disconnected tools",
    "Slow, manual lead qualification and routing",
    "Low visibility into buying intent across the funnel",
    "Difficulty prioritizing accounts for outbound",
    "Rising customer acquisition costs",
    "Sales and marketing misalignment on ICP",
]


def _rng(domain: str) -> random.Random:
    """A Random seeded deterministically from the domain (stable per company)."""
    seed = int(hashlib.sha256(domain.encode("utf-8")).hexdigest(), 16)
    return random.Random(seed)


def _infer_intent(company: Company) -> list[str]:
    """Mine recent_news for keyword-driven intent signals (de-duplicated,
    order-preserving)."""
    signals: list[str] = []
    haystack = " ".join(company.recent_news).lower()
    for keywords, signal in _NEWS_KEYWORDS:
        if any(kw in haystack for kw in keywords) and signal not in signals:
            signals.append(signal)
    return signals[:_MAX_SIGNALS]


def _outreach_email(company: Company, pain: str, tool: str) -> str:
    """Short, templated, personalized outreach email."""
    return (
        f"Subject: Helping {company.name} turn intent into pipeline\n\n"
        f"Hi {company.name} team,\n\n"
        f"I noticed {company.name} is scaling in {company.industry.lower()}. "
        f"Teams running on {tool} often hit one wall: {pain.lower()}. "
        f"We help GTM teams prioritize the accounts most likely to buy and "
        f"reach them before competitors do.\n\n"
        f"Worth a 15-minute look? Happy to share a tailored account list.\n\n"
        f"Best,\nThe Revenue Intelligence Team"
    )


def fallback_enrich(company: Company) -> Enrichment:
    rng = _rng(company.domain)

    # Technographics: industry stack, shuffled deterministically and trimmed.
    base_tech = list(_INDUSTRY_TECH.get(company.industry, _DEFAULT_TECH))
    rng.shuffle(base_tech)
    technographics = base_tech[:_MAX_TECH]

    # Intent from news; if none found, leave empty (scoring will reflect low intent).
    intent_signals = _infer_intent(company)
    intent_topics = [
        s.split(" — ")[0] for s in intent_signals  # the short label before the dash
    ][:_MAX_TOPICS]

    # Pain points: deterministic sample so each company looks distinct.
    pains = list(_PAIN_POINTS)
    rng.shuffle(pains)
    pain_points = pains[:_MAX_PAINS]

    outreach_email = _outreach_email(company, pain_points[0], technographics[0])

    gtm_recommendation = (
        f"Prioritize {company.name} with a value message centered on "
        f"{pain_points[0].lower()}. Lead with their {company.industry} peers and, "
        f"if engaged, route to an AE for an ICP-fit conversation."
    )

    return Enrichment(
        technographics=technographics,
        intent_signals=intent_signals,
        intent_topics=intent_topics,
        pain_points=pain_points,
        outreach_email=outreach_email,
        gtm_recommendation=gtm_recommendation,
        source=EnrichmentSource.FALLBACK,
    )
