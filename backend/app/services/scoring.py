"""ICP fit-scoring engine.

This is the analytical core of the product and must be **transparent**: it always
returns a per-dimension breakdown plus a human-readable rationale so the UI can
explain *why* an account scored as it did. It is a pure function of
(company, enrichment, ICP) — no I/O, no global state — which makes it trivially
unit-testable and safe to call from both the seed script and the live API.

Weights (from the ICP, summing to 100): industry 25, company_size 20,
revenue 15, geography 10, technographics 15, intent 15.

Partial-credit rule for the numeric bands (size, revenue): full points inside
the band, half points within 2x of either edge, zero beyond that. Technographics
and intent scale with how many distinct matches/signals exist.
"""

from app.models.company import Company
from app.models.enrichment import Enrichment
from app.models.fit import Fit, FitBreakdown, Tier
from app.models.icp import ICP

# Tier cutoffs on the 0-100 total.
HOT_THRESHOLD = 70
WARM_THRESHOLD = 45

# How many distinct matches/signals earn full marks on the scaled dimensions.
_FULL_TECH_MATCHES = 3
_FULL_INTENT_SIGNALS = 3


def _band_score(value: float, low: float, high: float, weight: int) -> tuple[float, str]:
    """Full weight inside [low, high]; half within 2x of an edge; else 0."""
    if low <= value <= high:
        return float(weight), "in target band"
    if low / 2 <= value < low:
        return weight / 2, "just below target band"
    if high < value <= high * 2:
        return weight / 2, "just above target band"
    return 0.0, "outside target band"


def score_account(company: Company, enrichment: Enrichment, icp: ICP) -> Fit:
    w = icp.weights
    notes: list[str] = []

    # ── Industry: categorical, all-or-nothing against the target verticals. ──
    if company.industry in icp.target_industries:
        industry_pts = float(w.industry)
        notes.append(f"Industry '{company.industry}' is a target vertical.")
    else:
        industry_pts = 0.0
        notes.append(f"Industry '{company.industry}' is outside target verticals.")

    # ── Company size (headcount) with partial-credit band. ──
    size_pts, size_label = _band_score(
        company.employee_count, icp.employee_min, icp.employee_max, w.company_size
    )
    notes.append(f"Headcount {company.employee_count:,} is {size_label}.")

    # ── Revenue with partial-credit band. ──
    rev_pts, rev_label = _band_score(
        company.estimated_revenue_usd, icp.revenue_min_usd, icp.revenue_max_usd, w.revenue
    )
    notes.append(f"Revenue ${company.estimated_revenue_usd:,} is {rev_label}.")

    # ── Geography: categorical against target countries. ──
    if company.country in icp.target_countries:
        geo_pts = float(w.geography)
        notes.append(f"HQ country '{company.country}' is a target market.")
    else:
        geo_pts = 0.0
        notes.append(f"HQ country '{company.country}' is outside target markets.")

    # ── Technographics: scale with distinct target tools detected. ──
    target_tech = {t.lower() for t in icp.target_technographics}
    detected = {t.lower() for t in enrichment.technographics}
    tech_matches = sorted(target_tech & detected)
    tech_pts = w.technographics * min(1.0, len(tech_matches) / _FULL_TECH_MATCHES)
    if tech_matches:
        notes.append(f"Uses {len(tech_matches)} target tool(s) in their stack.")
    else:
        notes.append("No target technographics detected.")

    # ── Intent: scale with distinct concrete signals. ──
    distinct_signals = {s.strip().lower() for s in enrichment.intent_signals if s.strip()}
    intent_pts = w.intent * min(1.0, len(distinct_signals) / _FULL_INTENT_SIGNALS)
    if distinct_signals:
        notes.append(f"{len(distinct_signals)} distinct intent signal(s) present.")
    else:
        notes.append("No active intent signals.")

    breakdown = FitBreakdown(
        industry=round(industry_pts, 1),
        company_size=round(size_pts, 1),
        revenue=round(rev_pts, 1),
        geography=round(geo_pts, 1),
        technographics=round(tech_pts, 1),
        intent=round(intent_pts, 1),
    )
    total = round(
        industry_pts + size_pts + rev_pts + geo_pts + tech_pts + intent_pts, 1
    )

    if total >= HOT_THRESHOLD:
        tier = Tier.HOT
    elif total >= WARM_THRESHOLD:
        tier = Tier.WARM
    else:
        tier = Tier.COLD

    return Fit(total=total, tier=tier, breakdown=breakdown, rationale=" ".join(notes))
