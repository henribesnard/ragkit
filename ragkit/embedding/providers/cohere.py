"""Cohere embedding provider using LiteLLM."""

from __future__ import annotations

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.embedding.providers.openai import _embed_with_litellm


class CohereEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self._dimensions = config.params.dimensions

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await _embed_with_litellm(self.config, texts)

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed([query])
        return results[0]
