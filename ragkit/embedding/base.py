"""Base classes for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""

    @property
    @abstractmethod
    def dimensions(self) -> int | None:
        """Return embedding dimension if known."""
