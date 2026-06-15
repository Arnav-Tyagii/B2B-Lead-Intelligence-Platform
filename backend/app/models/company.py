"""Firmographic data for a company — the raw input to enrichment + scoring."""

from pydantic import BaseModel, Field, computed_field

# Provenance labels for where the firmographics came from. "synthetic" is the
# generated book (default, backward-compatible with existing docs); real-data
# acquirers stamp their own source so the UI can surface and filter them.
SYNTHETIC_SOURCE = "synthetic"


class Company(BaseModel):
    name: str
    domain: str = Field(description="Canonical domain; also used as the account _id.")
    industry: str
    employee_count: int = Field(ge=0)
    estimated_revenue_usd: int = Field(ge=0, description="Estimated annual revenue in USD.")
    hq_location: str = Field(description="Human-readable HQ, e.g. 'San Francisco, CA'.")
    country: str
    founded_year: int | None = None
    description: str = ""
    # 1-2 short headlines per company; the fallback enricher mines these for
    # intent signals (funding / hiring / launch keywords).
    recent_news: list[str] = Field(default_factory=list)
    # Which acquirer produced these firmographics: "synthetic" (generated) or a
    # real source like "sec_edgar". Defaults to synthetic so older documents that
    # predate this field still load cleanly.
    data_source: str = Field(default=SYNTHETIC_SOURCE)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_real_data(self) -> bool:
        """Persisted (via model_dump) so the API can sort 'real data first' with a
        single null-safe descending index scan: True > False > missing."""
        return self.data_source != SYNTHETIC_SOURCE
