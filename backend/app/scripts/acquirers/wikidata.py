"""Wikidata augmenter — fills gaps SEC EDGAR leaves.

EDGAR has no founding year and only a terse SIC label. Wikidata (the structured
data behind Wikipedia) has both, via a free API. For each company we:
  1. search Wikidata for the entity by name (picking a company-like match),
  2. read its inception date (P571) → founding year, and its short description.

Best-effort and missing-safe: a no-match or odd value is skipped, never fatal.
We only set founded_year when it's currently empty, so authoritative data wins.
"""

import os
import time

import httpx

from app.core.logging import get_logger
from app.models.company import Company

logger = get_logger("acquirer.wikidata")

_SEARCH_URL = "https://www.wikidata.org/w/api.php"
_TIMEOUT = 15.0
_MIN_INTERVAL = 0.1
# Wikimedia's UA policy REQUIRES a descriptive agent with a contact, or it 403s.
# Override the contact via env in production.
_USER_AGENT = os.getenv(
    "WIKIDATA_USER_AGENT",
    "B2B-Lead-Intelligence/1.0 (https://github.com/arnavtyagi; 27.arnavtyagi@gmail.com)",
)

# Heuristic: prefer a search hit whose description reads like a business, so we
# don't attach (say) a film named "Oracle" to Oracle Corp.
_COMPANY_HINTS = (
    "company", "corporation", "business", "software", "manufacturer", "retailer",
    "retail", "bank", "technology", "enterprise", "brand", "airline",
    "semiconductor", "multinational", "firm", "platform",
)


class _RateLimiter:
    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last = time.monotonic()


def _search_entity(client: httpx.Client, name: str) -> tuple[str, str] | None:
    """Return (entity_id, short_description) for the best company-like match."""
    resp = client.get(_SEARCH_URL, params={
        "action": "wbsearchentities", "search": name, "language": "en",
        "format": "json", "type": "item", "limit": 5,
    })
    resp.raise_for_status()
    results = resp.json().get("search", [])
    if not results:
        return None
    for r in results:
        desc = (r.get("description") or "").lower()
        if any(h in desc for h in _COMPANY_HINTS):
            return r["id"], r.get("description", "")
    # No obviously-corporate hit: fall back to the top result.
    return results[0]["id"], results[0].get("description", "")


def _inception_year(client: httpx.Client, entity_id: str) -> int | None:
    resp = client.get(_SEARCH_URL, params={
        "action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json",
    })
    resp.raise_for_status()
    claims = resp.json().get("entities", {}).get(entity_id, {}).get("claims", {})
    try:
        time_str = claims["P571"][0]["mainsnak"]["datavalue"]["value"]["time"]
    except (KeyError, IndexError, TypeError):
        return None
    # Format like "+1976-04-01T00:00:00Z"; pull the year.
    try:
        year = int(time_str[1:5])
    except ValueError:
        return None
    return year if 1700 <= year <= 2100 else None


def apply_wikidata(companies: list[Company], limit: int | None = None) -> int:
    """Augment companies in place with founding year + a richer description.
    Returns how many were augmented."""
    limiter = _RateLimiter(_MIN_INTERVAL)
    augmented = 0
    headers = {"User-Agent": _USER_AGENT}

    with httpx.Client(headers=headers, timeout=_TIMEOUT) as client:
        for company in companies:
            if limit is not None and augmented >= limit:
                break
            limiter.wait()
            try:
                match = _search_entity(client, company.name)
                if match is None:
                    continue
                entity_id, description = match
                limiter.wait()
                year = _inception_year(client, entity_id)
            except httpx.HTTPError as exc:
                logger.warning("Wikidata fetch failed for %s: %s", company.name, exc)
                continue

            changed = False
            # Only fill founded_year if EDGAR didn't provide it.
            if company.founded_year is None and year is not None:
                company.founded_year = year
                changed = True
            # Lead the description with Wikidata's crisp summary, if present.
            if description and description.lower() not in company.description.lower():
                # Upper-case only the first char so acronyms (US, IT, SaaS) survive.
                lead = description[0].upper() + description[1:]
                company.description = f"{lead}. {company.description}"
                changed = True
            if changed:
                augmented += 1

    logger.info("Wikidata: augmented %d/%d companies.", augmented, len(companies))
    return augmented
