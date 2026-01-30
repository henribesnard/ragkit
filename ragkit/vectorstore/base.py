"""Base vector store definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from ragkit.models import Chunk


class SearchResult(BaseModel):
    chunk: Chunk
    score: float


class BaseVectorStore(ABC):
    @abstractmethod
    async def add(self, chunks: list[Chunk]) -> None:
        """Add chunks to the store."""

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search chunks by embedding similarity."""

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete chunks by id."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear the vector store."""
