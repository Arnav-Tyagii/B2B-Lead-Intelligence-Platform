"""SEC EDGAR acquirer — authoritative firmographics from public filings.

The U.S. SEC publishes every filer's data as a free JSON API (`data.sec.gov`).
This is NOT web scraping: we consume official structured endpoints. There is no
daily quota — the only rule is a politeness cap of ~10 requests/second and a
descriptive `User-Agent` carrying a contact (requests without one get 403'd).

Per company we hit two endpoints:
  - submissions/CIK##########.json  → legal name, SIC industry, HQ city/state
  - api/xbrl/companyfacts/CIK#####.json → revenue (and, when tagged, employees)

Everything is best-effort and missing-safe: a field we can't find falls back to a
sensible default, and a company that errors entirely is logged and skipped — one
bad filing never aborts the run.
"""

import json
import os
import time

import httpx

from app.core.logging import get_logger
from app.models.company import Company
from app.scripts.acquirers.seed_universe import COMPANY_UNIVERSE

logger = get_logger("acquirer.sec")

# SEC requires a descriptive UA with a contact. Override via env in production.
_USER_AGENT = os.getenv(
    "SEC_USER_AGENT", "B2B-Lead-Intelligence/1.0 (contact: 27.arnavtyagi@gmail.com)"
)
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Stay comfortably under the 10 req/s ceiling.
_MIN_REQUEST_INTERVAL = 0.15
_TIMEOUT = 20.0

# us-gaap revenue concepts in order of preference; companies tag one of these.
_REVENUE_CONCEPTS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
)

# SIC descriptions are verbose ("Services-Prepackaged Software"); map them onto
# the ICP taxonomy (first keyword hit wins) so the industry score is meaningful.
_SIC_KEYWORDS: list[tuple[str, str]] = [
    ("semiconductor", "Manufacturing"),
    ("security", "Cybersecurity"),
    ("prepackaged software", "SaaS"),
    ("computer programming", "SaaS"),
    ("software", "SaaS"),
    ("data processing", "Data & Analytics"),
    ("information retrieval", "Data & Analytics"),
    ("computer", "Cloud Infrastructure"),
    ("advertising", "MarTech"),
    ("finance", "FinTech"),
    ("bank", "FinTech"),
    ("credit", "FinTech"),
    ("retail", "E-commerce"),
    ("catalog", "E-commerce"),
    ("health", "Healthcare"),
]

# Minimal US-state set so we can classify country without another API call.
_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
_COUNTRY_CODES = {"US": "United States", "L2": "United Kingdom", "A6": "Australia",
                  "F4": "Canada", "Q2": "India", "2M": "Germany", "U0": "Singapore"}


def _map_industry(sic_description: str) -> str:
    desc = (sic_description or "").lower()
    for keyword, industry in _SIC_KEYWORDS:
        if keyword in desc:
            return industry
    # Unknown SIC: keep the raw description (title-cased) rather than guess.
    return sic_description.title() if sic_description else "Unknown"


def _clean_name(raw: str) -> str:
    """EDGAR names are often shouty ('SALESFORCE, INC.'). Tidy for display."""
    name = raw.strip().rstrip(".")
    for suffix in (", INC", ", INC.", " INC", ", CORP", " CORP", ", LTD", " PLC"):
        if name.upper().endswith(suffix):
            name = name[: -len(suffix)].rstrip(", ")
            break
    return name.title() if name.isupper() else name


def _latest_annual_value(facts: dict, namespace: str, concept: str) -> int | None:
    """Pick the most recent ANNUAL (10-K/20-F) USD value for a concept, if tagged."""
    try:
        units = facts["facts"][namespace][concept]["units"]["USD"]
    except (KeyError, TypeError):
        return None
    annual = [u for u in units if u.get("form") in ("10-K", "20-F") and u.get("val") is not None]
    if not annual:
        return None
    # 'end' is an ISO date string; max() gives the latest fiscal year end.
    latest = max(annual, key=lambda u: u.get("end", ""))
    try:
        return int(latest["val"])
    except (TypeError, ValueError):
        return None


def _employee_count(facts: dict) -> int | None:
    """Headcount is rarely XBRL-tagged; scan dei for any *Employee* concept."""
    dei = facts.get("facts", {}).get("dei", {})
    for concept, payload in dei.items():
        if "Employee" not in concept:
            continue
        for unit_values in payload.get("units", {}).values():
            vals = [v.get("val") for v in unit_values if isinstance(v.get("val"), (int, float))]
            if vals:
                return int(max(vals))
    return None


class _RateLimiter:
    """Spaces requests to honour SEC's ~10 req/s fair-use limit."""

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last = time.monotonic()


class SECEdgarAcquirer:
    name = "sec_edgar"

    def __init__(self) -> None:
        self._limiter = _RateLimiter(_MIN_REQUEST_INTERVAL)

    def acquire(self, count: int) -> list[Company]:
        headers = {"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"}
        with httpx.Client(headers=headers, timeout=_TIMEOUT) as client:
            cik_by_ticker = self._load_cik_map(client)
            if not cik_by_ticker:
                logger.error("Could not load SEC ticker map; no companies acquired.")
                return []

            companies: list[Company] = []
            for ticker, domain, emp_hint in COMPANY_UNIVERSE[:count]:
                cik = cik_by_ticker.get(ticker.upper())
                if cik is None:
                    logger.warning("No CIK for ticker %s; skipping.", ticker)
                    continue
                company = self._acquire_one(client, ticker, domain, emp_hint, cik)
                if company is not None:
                    companies.append(company)

            logger.info("SEC EDGAR: acquired %d/%d companies.",
                        len(companies), min(count, len(COMPANY_UNIVERSE)))
            return companies

    # ── internals ──

    def _get_json(self, client: httpx.Client, url: str) -> dict | None:
        self._limiter.wait()
        try:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            logger.warning("SEC fetch failed (%s): %s", url, exc)
            return None

    def _load_cik_map(self, client: httpx.Client) -> dict[str, str]:
        """ticker (upper) → zero-padded 10-digit CIK string used by the API paths."""
        data = self._get_json(client, _TICKERS_URL)
        if not data:
            return {}
        return {
            row["ticker"].upper(): f"{int(row['cik_str']):010d}"
            for row in data.values()
        }

    def _acquire_one(
        self, client: httpx.Client, ticker: str, domain: str, emp_hint: int, cik: str
    ) -> Company | None:
        submissions = self._get_json(client, _SUBMISSIONS_URL.format(cik=cik))
        if not submissions:
            return None  # no filer record → skip

        facts = self._get_json(client, _FACTS_URL.format(cik=cik)) or {}

        name = _clean_name(submissions.get("name", ticker))
        industry = _map_industry(submissions.get("sicDescription", ""))
        hq_location, country = self._parse_address(submissions)

        revenue = 0
        for concept in _REVENUE_CONCEPTS:
            value = _latest_annual_value(facts, "us-gaap", concept)
            if value:
                revenue = value
                break

        # Authoritative headcount if tagged; otherwise the curated hint so the
        # company-size score isn't artificially zeroed.
        employees = _employee_count(facts) or emp_hint

        description = (
            f"{name} ({ticker}) is a U.S. public company classified by the SEC under "
            f"\"{submissions.get('sicDescription', 'n/a')}\", headquartered in "
            f"{hq_location}. Firmographics sourced from SEC EDGAR filings."
        )

        return Company(
            name=name,
            domain=domain,
            industry=industry,
            employee_count=max(0, employees),
            estimated_revenue_usd=max(0, revenue),
            hq_location=hq_location,
            country=country,
            founded_year=None,  # not reliably available in EDGAR structured data
            description=description,
            recent_news=[],  # populated by the Greenhouse/Lever intent overlay
            data_source=self.name,
        )

    @staticmethod
    def _parse_address(submissions: dict) -> tuple[str, str]:
        biz = (submissions.get("addresses") or {}).get("business") or {}
        city = (biz.get("city") or "").title()
        region = (biz.get("stateOrCountry") or "").upper()
        if region in _US_STATES:
            country = "United States"
        else:
            country = _COUNTRY_CODES.get(region, "United States")
        hq = ", ".join(part for part in (city, region) if part) or "Unknown"
        return hq, country


def acquire(count: int = 50) -> list[Company]:
    """Module-level convenience used by the registry and the CLI preview."""
    return SECEdgarAcquirer().acquire(count)


if __name__ == "__main__":  # quick manual check: python -m app.scripts.acquirers.sec_edgar
    from app.core.logging import configure_logging

    configure_logging()
    for c in acquire(5):
        print(f"{c.name:24} {c.industry:18} {c.country:14} "
              f"emp={c.employee_count:>9,} rev=${c.estimated_revenue_usd:,}")
