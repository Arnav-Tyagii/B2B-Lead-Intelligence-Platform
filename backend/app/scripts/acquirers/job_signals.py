"""Hiring-intent overlay from public ATS boards (Greenhouse + Lever).

Many companies expose their open roles as public JSON via their applicant-tracking
system. Open headcount is a textbook GTM *intent signal*, and the job titles hint
at the tech stack. We turn that into one or two headlines written onto the
company's `recent_news` — which the EXISTING fallback enricher already mines for
the "hiring" keyword, so the signal flows through the normal pipeline untouched.

Coverage is partial BY NATURE: only companies that (a) use Greenhouse/Lever and
(b) whose board token we know get intent. Everyone else is left as-is — that's
honest, and the score simply reflects less intent. Tokens below are best-effort;
a 404 is logged and skipped, and any token is trivial to correct.
"""

import time

import httpx

from app.core.logging import get_logger
from app.models.company import Company

logger = get_logger("acquirer.intent")

_GREENHOUSE_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
_LEVER_URL = "https://api.lever.co/v0/postings/{token}?mode=json"
_TIMEOUT = 15.0
_MIN_INTERVAL = 0.2
_MAX_TITLES = 3  # how many sample role titles to fold into the headline

# domain -> (provider, board_token). Best-effort; tokens are typically the
# company slug. A wrong/stale token simply 404s and is skipped, so this list is
# safe to grow generously — coverage improves, nothing breaks.
_ATS_BOARDS: dict[str, tuple[str, str]] = {
    # ── confirmed-ish Greenhouse boards ──
    "datadoghq.com": ("greenhouse", "datadog"),
    "cloudflare.com": ("greenhouse", "cloudflare"),
    "gitlab.com": ("greenhouse", "gitlab"),
    "coinbase.com": ("greenhouse", "coinbase"),
    "airbnb.com": ("greenhouse", "airbnb"),
    "doordash.com": ("greenhouse", "doordash"),
    "lyft.com": ("greenhouse", "lyft"),
    "dropbox.com": ("greenhouse", "dropbox"),
    "asana.com": ("greenhouse", "asana"),
    "robinhood.com": ("greenhouse", "robinhood"),
    "snowflake.com": ("greenhouse", "snowflakecomputing"),
    "elastic.co": ("greenhouse", "elastic"),
    "confluent.io": ("greenhouse", "confluent"),
    "twilio.com": ("greenhouse", "twilio"),
    "okta.com": ("greenhouse", "okta"),
    "mongodb.com": ("greenhouse", "mongodb"),
    "braze.com": ("greenhouse", "braze"),
    "monday.com": ("greenhouse", "mondaycom"),
    # ── additional Greenhouse candidates (best-effort tokens) ──
    "pinterest.com": ("greenhouse", "pinterest"),
    "snap.com": ("greenhouse", "snap"),
    "roblox.com": ("greenhouse", "roblox"),
    "unity.com": ("greenhouse", "unitytechnologies"),
    "palantir.com": ("greenhouse", "palantir"),
    "uipath.com": ("greenhouse", "uipath"),
    "hubspot.com": ("greenhouse", "hubspot"),
    "shopify.com": ("greenhouse", "shopify"),
    "zscaler.com": ("greenhouse", "zscaler"),
    "crowdstrike.com": ("greenhouse", "crowdstrike"),
    "sentinelone.com": ("greenhouse", "sentinelone"),
    "digitalocean.com": ("greenhouse", "digitalocean"),
    "doximity.com": ("greenhouse", "doximity"),
    "affirm.com": ("greenhouse", "affirm"),
    "toasttab.com": ("greenhouse", "toast"),
    "pagerduty.com": ("greenhouse", "pagerduty"),
    "fastly.com": ("greenhouse", "fastly"),
    "nutanix.com": ("greenhouse", "nutanix"),
    "rapid7.com": ("greenhouse", "rapid7"),
    "tenable.com": ("greenhouse", "tenable"),
    "cyberark.com": ("greenhouse", "cyberark"),
    "procore.com": ("greenhouse", "procore"),
    "smartsheet.com": ("greenhouse", "smartsheet"),
    "freshworks.com": ("greenhouse", "freshworks"),
    "bill.com": ("greenhouse", "billcom"),
    "gusto.com": ("greenhouse", "gusto"),
    # ── Lever boards ──
    "netflix.com": ("lever", "netflix"),
    "spotify.com": ("lever", "spotify"),
}


class _RateLimiter:
    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last = time.monotonic()


def _fetch_greenhouse(client: httpx.Client, token: str) -> tuple[int, list[str]]:
    resp = client.get(_GREENHOUSE_URL.format(token=token))
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    titles = [j.get("title", "").strip() for j in jobs if j.get("title")]
    return len(jobs), titles


def _fetch_lever(client: httpx.Client, token: str) -> tuple[int, list[str]]:
    resp = client.get(_LEVER_URL.format(token=token))
    resp.raise_for_status()
    postings = resp.json()
    titles = [p.get("text", "").strip() for p in postings if p.get("text")]
    return len(postings), titles


def _build_headlines(count: int, titles: list[str]) -> list[str]:
    """Phrase open roles as intent headlines. The word 'hiring' is deliberate —
    it's the token the fallback enricher keys on for a hiring intent signal."""
    if count <= 0:
        return []
    sample = ", ".join(titles[:_MAX_TITLES])
    headlines = [f"Actively hiring across {count} open roles."]
    if sample:
        headlines.append(f"Open positions include: {sample}.")
    return headlines


def apply_intent(companies: list[Company], limit: int | None = None) -> int:
    """Mutate companies in place, adding hiring-intent headlines to recent_news
    for those with a known public board. Returns how many were augmented."""
    limiter = _RateLimiter(_MIN_INTERVAL)
    augmented = 0
    headers = {"User-Agent": "B2B-Lead-Intelligence/1.0 (intent overlay)"}

    with httpx.Client(headers=headers, timeout=_TIMEOUT) as client:
        for company in companies:
            board = _ATS_BOARDS.get(company.domain)
            if board is None:
                continue
            if limit is not None and augmented >= limit:
                break
            provider, token = board
            limiter.wait()
            try:
                if provider == "greenhouse":
                    count, titles = _fetch_greenhouse(client, token)
                else:
                    count, titles = _fetch_lever(client, token)
            except httpx.HTTPError as exc:
                logger.warning("ATS fetch failed for %s (%s/%s): %s",
                               company.domain, provider, token, exc)
                continue

            headlines = _build_headlines(count, titles)
            if headlines:
                # Prepend so the live hiring signal leads any existing news.
                company.recent_news = headlines + company.recent_news
                augmented += 1
                logger.info("Intent: %s — %d open roles via %s.",
                            company.domain, count, provider)

    logger.info("Intent overlay: augmented %d/%d companies.", augmented, len(companies))
    return augmented
