"""News & buzz overlay — real recent headlines + community mention volume.

Two free, key-less sources:
  - Google News RSS  → recent headlines about the company (real "From the Wire").
  - Hacker News (Algolia) → count of recent story mentions = a buzz/intent proxy.

Headlines land in `recent_news`, which the existing fallback enricher mines for
funding / hiring / launch keywords → intent signals. So real news flows straight
into the score with no pipeline change. Best-effort and missing-safe throughout.
"""

import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

from app.core.logging import get_logger
from app.models.company import Company

logger = get_logger("acquirer.news")

_GNEWS_URL = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
_HN_URL = "https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story&numericFilters=points%3E5"
_TIMEOUT = 15.0
_MIN_INTERVAL = 0.2
_MAX_HEADLINES = 4


class _RateLimiter:
    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last = time.monotonic()


def _clean_headline(title: str) -> str:
    # Google News titles end with " - Publisher"; drop the trailing source.
    return title.rsplit(" - ", 1)[0].strip() if " - " in title else title.strip()


def _fetch_news(client: httpx.Client, name: str) -> list[str]:
    # Quote the name so multi-word companies match as a phrase.
    resp = client.get(_GNEWS_URL.format(q=quote_plus(f'"{name}"')))
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    titles = [
        _clean_headline(item.findtext("title") or "")
        for item in root.iterfind(".//item")
    ]
    return [t for t in titles if t][:_MAX_HEADLINES]


def _fetch_hn_buzz(client: httpx.Client, name: str) -> int:
    resp = client.get(_HN_URL.format(q=quote_plus(name)))
    resp.raise_for_status()
    return int(resp.json().get("nbHits", 0))


def apply_news(companies: list[Company], limit: int | None = None) -> int:
    """Append real news headlines (+ a buzz line) to each company's recent_news.
    Returns how many were augmented."""
    limiter = _RateLimiter(_MIN_INTERVAL)
    augmented = 0
    headers = {"User-Agent": "B2B-Lead-Intelligence/1.0 (news overlay)"}

    with httpx.Client(headers=headers, timeout=_TIMEOUT, follow_redirects=True) as client:
        for company in companies:
            if limit is not None and augmented >= limit:
                break
            limiter.wait()
            try:
                headlines = _fetch_news(client, company.name)
            except (httpx.HTTPError, ET.ParseError) as exc:
                logger.warning("News fetch failed for %s: %s", company.name, exc)
                headlines = []

            buzz_line: list[str] = []
            try:
                limiter.wait()
                hits = _fetch_hn_buzz(client, company.name)
                if hits > 0:
                    buzz_line = [f"{hits} recent Hacker News mentions — active community buzz."]
            except httpx.HTTPError:
                pass  # buzz is a bonus; ignore failures

            additions = headlines + buzz_line
            if additions:
                # Append after any hiring signals so they don't get buried.
                company.recent_news = company.recent_news + additions
                augmented += 1

    logger.info("News overlay: augmented %d/%d companies.", augmented, len(companies))
    return augmented
