"""LiteLLM-based embedder supporting any provider LiteLLM handles."""

from __future__ import annotations

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.exceptions import EmbeddingError


class LiteLLMEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self._dimensions = config.params.dimensions

    @property
    def dimensions(self) -> int:
        if self._dimensions:
            return self._dimensions
        raise ValueError("dimensions must be set for litellm embedder")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            import litellm
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError("litellm is required for embeddings") from exc

        response = await litellm.aembedding(
            model=self.config.model,
            input=texts,
            api_key=self.config.api_key,
        )
        return [item["embedding"] for item in response.data]

    async def embed_query(self, query: str) -> list[float]:
        result = await self.embed([query])
        return result[0]
