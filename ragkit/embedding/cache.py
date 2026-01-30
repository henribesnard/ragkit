"""Embedding cache utilities."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ragkit.embedding.base import BaseEmbedder


class EmbeddingCache:
    def __init__(self, backend: str = "memory", ttl: int | None = None, path: Path | None = None):
        self.backend = backend
        self.ttl = ttl
        self.path = path or Path(".ragkit") / "embedding_cache.json"
        self._memory: dict[str, tuple[list[float], float]] = {}
        if self.backend == "disk":
            self._memory.update(self._load_disk())

    async def get(self, text_hash: str) -> list[float] | None:
        entry = self._memory.get(text_hash)
        if not entry:
            return None
        embedding, timestamp = entry
        if self.ttl is not None and time.time() - timestamp > self.ttl:
            self._memory.pop(text_hash, None)
            return None
        return embedding

    async def set(self, text_hash: str, embedding: list[float]) -> None:
        self._memory[text_hash] = (embedding, time.time())
        if self.backend == "disk":
            self._write_disk()

    def _load_disk(self) -> dict[str, tuple[list[float], float]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(raw, dict):
            return {}
        loaded: dict[str, tuple[list[float], float]] = {}
        for key, value in raw.items():
            if isinstance(value, dict) and "embedding" in value and "ts" in value:
                loaded[key] = (value["embedding"], float(value["ts"]))
        return loaded

    def _write_disk(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {}
        for key, (embedding, ts) in self._memory.items():
            payload[key] = {"embedding": embedding, "ts": ts}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class CachedEmbedder(BaseEmbedder):
    def __init__(self, embedder: BaseEmbedder, cache: EmbeddingCache):
        self.embedder = embedder
        self.cache = cache

    @property
    def dimensions(self) -> int | None:
        return self.embedder.dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        missing_texts: list[str] = []
        missing_indices: list[int] = []

        for idx, text in enumerate(texts):
            cached = await self.cache.get(_hash_text(text))
            if cached is None:
                missing_texts.append(text)
                missing_indices.append(idx)
                results.append([])
            else:
                results.append(cached)

        if missing_texts:
            new_embeddings = await self.embedder.embed(missing_texts)
            for offset, embedding in enumerate(new_embeddings):
                text = missing_texts[offset]
                index = missing_indices[offset]
                await self.cache.set(_hash_text(text), embedding)
                results[index] = embedding

        return results

    async def embed_query(self, query: str) -> list[float]:
        cached = await self.cache.get(_hash_text(query))
        if cached is not None:
            return cached
        embedding = await self.embedder.embed_query(query)
        await self.cache.set(_hash_text(query), embedding)
        return embedding


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
