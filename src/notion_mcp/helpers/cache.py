"""Simple in-memory cache for database schemas."""

import time
from typing import Any, Dict, Optional


class TTLCache:
    """Time-to-live cache for storing computed values temporarily."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._store: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        timestamp, value = self._store[key]
        if time.time() - timestamp > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


schema_cache = TTLCache(ttl_seconds=3600)