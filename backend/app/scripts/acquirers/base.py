"""The acquisition interface.

An *acquirer* is anything that can produce a list of `Company` firmographics for
the seed pipeline. Formalising it as a Protocol is the whole point of this layer:
the downstream pipeline (enrich → score → upsert) is completely source-agnostic,
so swapping the synthetic generator for a real source (SEC EDGAR, …) is a one-line
change in seed.py. New sources only have to satisfy this contract.
"""

from typing import Protocol, runtime_checkable

from app.models.company import Company


@runtime_checkable
class Acquirer(Protocol):
    #: Stable identifier used by the registry and logged in seed reports.
    name: str

    def acquire(self, count: int) -> list[Company]:
        """Return up to `count` companies. Implementations MUST be resilient: a
        single bad record/page is logged and skipped, never fatal to the run."""
        ...
