"""Tiny in-process TTL cache.

Read-heavy endpoints (/stats, /accounts list) are cached briefly to spare the M0
cluster repeated identical aggregations during dashboard browsing. This is a
deliberately simple per-process cache — fine for a single free-tier instance.
A horizontally-scaled deployment would swap this for Redis behind the same API.
"""

import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.monotonic():
            self._store.pop(key, None)  # lazily evict expired entries
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        """Invalidate everything — called after a write (e.g. /enrich upsert)."""
        self._store.clear()
