"""In-memory LRU cache backend."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float | None


class MemoryBackend:
    """Simple LRU cache with TTL."""

    def __init__(self, max_items: int = 1024, default_ttl: int | None = None) -> None:
        self.max_items = max(1, max_items)
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at is not None and entry.expires_at < time.monotonic():
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None) -> None:
        async with self._lock:
            expires_at = None
            ttl_value = ttl if ttl is not None else self.default_ttl
            if ttl_value and ttl_value > 0:
                expires_at = time.monotonic() + ttl_value
            self._store[key] = _Entry(value=value, expires_at=expires_at)
            self._store.move_to_end(key)
            await self._evict_if_needed()

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def _evict_if_needed(self) -> None:
        while len(self._store) > self.max_items:
            self._store.popitem(last=False)
