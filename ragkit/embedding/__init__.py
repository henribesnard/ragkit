"""Embedding factory and exports."""

from __future__ import annotations

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.embedding.cache import CachedEmbedder, EmbeddingCache
from ragkit.embedding.providers.cohere import CohereEmbedder
from ragkit.embedding.providers.litellm import LiteLLMEmbedder
from ragkit.embedding.providers.ollama import OllamaEmbedder
from ragkit.embedding.providers.openai import OpenAIEmbedder
from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder


def create_embedder(config: EmbeddingModelConfig) -> BaseEmbedder:
    if config.provider == "openai":
        embedder: BaseEmbedder = OpenAIEmbedder(config)
    elif config.provider == "ollama":
        embedder = OllamaEmbedder(config)
    elif config.provider == "cohere":
        embedder = CohereEmbedder(config)
    elif config.provider == "litellm":
        embedder = LiteLLMEmbedder(config)
    elif config.provider == "onnx_local":
        embedder = ONNXLocalEmbedder(config)
    else:
        raise ValueError(f"Unknown embedding provider: {config.provider}")

    if config.cache.enabled:
        cache = EmbeddingCache(backend=config.cache.backend)
        return CachedEmbedder(embedder, cache)

    return embedder


__all__ = [
    "BaseEmbedder",
    "EmbeddingCache",
    "CachedEmbedder",
    "OpenAIEmbedder",
    "OllamaEmbedder",
    "CohereEmbedder",
    "LiteLLMEmbedder",
    "ONNXLocalEmbedder",
    "create_embedder",
]
