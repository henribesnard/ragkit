"""Query cache with exact, fuzzy, or semantic matching."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from ragkit.cache.backends import build_backend
from ragkit.cache.backends.base import CacheBackend
from ragkit.cache.semantic_matcher import SemanticMatcher
from ragkit.config.schema_v2 import CacheConfigV2


class QueryCache:
    """Cache query responses."""

    def __init__(
        self,
        config: CacheConfigV2,
        backend: CacheBackend | None = None,
        semantic_matcher: SemanticMatcher | None = None,
    ) -> None:
        self.config = config
        self.backend = backend or build_backend(
            config,
            size_mb=config.query_cache_size_mb,
            ttl=config.query_cache_ttl,
        )
        self.semantic_matcher = semantic_matcher

    async def get(self, query: str) -> Any | None:
        key = await self._resolve_key(query)
        if not key:
            return None
        return await self.backend.get(key)

    async def set(self, query: str, value: Any) -> None:
        key = self._hash_key(self._normalized_key(query))
        await self.backend.set(key, value, ttl=self.config.query_cache_ttl)
        if self.config.cache_key_strategy == "semantic" and self.semantic_matcher:
            await self.semantic_matcher.add(key, query, ttl=self.config.query_cache_ttl)

    async def clear(self) -> None:
        await self.backend.clear()

    async def _resolve_key(self, query: str) -> str | None:
        strategy = self.config.cache_key_strategy
        if strategy == "exact":
            return self._hash_key(query)
        if strategy == "fuzzy":
            return self._hash_key(self._normalize_query(query))
        if strategy == "semantic" and self.semantic_matcher:
            matched = await self.semantic_matcher.find(query)
            if matched:
                return matched
            return self._hash_key(self._normalized_key(query))
        return self._hash_key(query)

    def _normalized_key(self, query: str) -> str:
        if self.config.cache_key_strategy == "fuzzy":
            return self._normalize_query(query)
        return query

    @staticmethod
    def _hash_key(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _normalize_query(self, query: str) -> str:
        text = query.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        tokens = [tok for tok in text.split() if tok not in _STOPWORDS]
        return " ".join(tokens)


_STOPWORDS = {
    "the",
    "is",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "for",
    "on",
    "how",
    "what",
}
