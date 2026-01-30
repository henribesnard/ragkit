"""OpenAI embedding provider using LiteLLM."""

from __future__ import annotations

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.exceptions import EmbeddingError


class OpenAIEmbedder(BaseEmbedder):
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


async def _embed_with_litellm(config: EmbeddingModelConfig, texts: list[str]) -> list[list[float]]:
    try:
        import litellm
    except Exception as exc:  # noqa: BLE001
        raise EmbeddingError("litellm is required for embeddings") from exc

    batch_size = config.params.batch_size or len(texts)
    embeddings: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        try:
            response = await litellm.aembedding(
                model=config.model,
                input=batch,
                api_key=config.api_key,
                dimensions=config.params.dimensions,
            )
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError(str(exc)) from exc
        embeddings.extend(_extract_embeddings(response))

    return embeddings


def _extract_embeddings(response: object) -> list[list[float]]:
    if isinstance(response, dict):
        data = response.get("data", [])
    else:
        data = getattr(response, "data", [])
    embeddings: list[list[float]] = []
    for item in data:
        if isinstance(item, dict):
            embedding = item.get("embedding")
        else:
            embedding = getattr(item, "embedding", None)
        if embedding is None:
            continue
        embeddings.append(list(embedding))
    return embeddings
