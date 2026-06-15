"""GenAI-derived (or fallback-derived) intelligence about an account.

`source` records provenance so the UI can honestly show whether a record came
from Gemini or the deterministic fallback enricher.
"""

from enum import Enum

from pydantic import BaseModel, Field


class EnrichmentSource(str, Enum):
    GEMINI = "gemini"
    FALLBACK = "fallback"


class Enrichment(BaseModel):
    technographics: list[str] = Field(default_factory=list)
    intent_signals: list[str] = Field(default_factory=list)
    intent_topics: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    outreach_email: str = ""
    gtm_recommendation: str = ""
    source: EnrichmentSource = EnrichmentSource.FALLBACK
