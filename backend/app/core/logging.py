"""Structured-ish logging setup.

Kept intentionally simple (stdlib logging) so it works the same locally and on
Render's log stream. Call `configure_logging()` once at app startup. We use a
single consistent format so logs are greppable in production.
"""

import logging

from app.config import get_settings

_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Convenience accessor so modules don't each import logging directly."""
    return logging.getLogger(name)
