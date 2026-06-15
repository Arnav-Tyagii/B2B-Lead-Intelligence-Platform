"""Synthetic acquirer — the default source, kept as a zero-dependency fallback.

This is a thin adapter over the existing `generate_companies()` so the generated
book satisfies the same `Acquirer` interface as the real sources. `generate_data`
itself is untouched, so nothing about the existing seed behaviour changes.
"""

from app.models.company import Company
from app.scripts.generate_data import generate_companies


class SyntheticAcquirer:
    name = "synthetic"

    def acquire(self, count: int) -> list[Company]:
        # generate_companies already stamps data_source="synthetic" via the model
        # default, so these flow through filters/sorts as non-real records.
        return generate_companies(count)
