"""Acquirer registry — the single lookup `seed.py` uses to pick a data source.

Keeping the mapping here means scrapers/clients aren't imported anywhere else in
the app (they're offline-seed-only, never on the live request path).
"""

from app.scripts.acquirers.base import Acquirer
from app.scripts.acquirers.sec_edgar import SECEdgarAcquirer
from app.scripts.acquirers.synthetic import SyntheticAcquirer

_REGISTRY: dict[str, Acquirer] = {
    SyntheticAcquirer.name: SyntheticAcquirer(),
    SECEdgarAcquirer.name: SECEdgarAcquirer(),
}

# CLI-friendly aliases.
SOURCE_CHOICES = ("synthetic", "sec")
_ALIASES = {"sec": "sec_edgar"}


def get_acquirer(name: str) -> Acquirer:
    """Resolve a source name (or alias) to its acquirer; raises on unknown."""
    resolved = _ALIASES.get(name, name)
    try:
        return _REGISTRY[resolved]
    except KeyError:
        raise ValueError(
            f"Unknown acquirer '{name}'. Choices: {', '.join(SOURCE_CHOICES)}"
        ) from None


__all__ = ["Acquirer", "get_acquirer", "SOURCE_CHOICES"]
