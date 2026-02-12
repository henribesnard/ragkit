"""Cache backend protocol."""

from __future__ import annotations

from typing import Any, Protocol


class CacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl: int | None) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def clear(self) -> None: ...
