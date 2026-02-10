"""Redis cache backend."""

from __future__ import annotations

import pickle
from typing import Any


class RedisBackend:
    """Redis-backed cache."""

    def __init__(self, url: str, compress: bool = False, algorithm: str = "lz4") -> None:
        self.url = url
        self.compress = compress
        self.algorithm = algorithm
        self._client = None

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        data = await client.get(key)
        if data is None:
            return None
        raw = _decompress(data, self.compress, self.algorithm)
        return pickle.loads(raw)

    async def set(self, key: str, value: Any, ttl: int | None) -> None:
        client = await self._get_client()
        raw = pickle.dumps(value)
        payload = _compress(raw, self.compress, self.algorithm)
        if ttl and ttl > 0:
            await client.setex(key, ttl, payload)
        else:
            await client.set(key, payload)

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def clear(self) -> None:
        client = await self._get_client()
        await client.flushdb()

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as redis  # type: ignore
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("redis package is required for RedisBackend") from exc
            self._client = redis.from_url(self.url)
        return self._client


def _compress(data: bytes, enabled: bool, algorithm: str) -> bytes:
    if not enabled:
        return data
    if algorithm == "gzip":
        import gzip

        return gzip.compress(data)
    if algorithm == "zstd":
        try:
            import zstandard as zstd  # type: ignore
        except Exception:  # noqa: BLE001
            return data
        return zstd.ZstdCompressor().compress(data)
    if algorithm == "lz4":
        try:
            import lz4.frame  # type: ignore
        except Exception:  # noqa: BLE001
            return data
        return lz4.frame.compress(data)
    return data


def _decompress(data: bytes, enabled: bool, algorithm: str) -> bytes:
    if not enabled:
        return data
    if algorithm == "gzip":
        import gzip

        return gzip.decompress(data)
    if algorithm == "zstd":
        try:
            import zstandard as zstd  # type: ignore
        except Exception:  # noqa: BLE001
            return data
        return zstd.ZstdDecompressor().decompress(data)
    if algorithm == "lz4":
        try:
            import lz4.frame  # type: ignore
        except Exception:  # noqa: BLE001
            return data
        return lz4.frame.decompress(data)
    return data
