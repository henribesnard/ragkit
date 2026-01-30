"""Base vector store definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ragkit.models import Chunk


class SearchResult(BaseModel):
    chunk: Chunk
    score: float


class VectorStoreStats(BaseModel):
    provider: str
    collection_name: str
    vector_count: int
    details: dict[str, Any] = Field(default_factory=dict)


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

    @abstractmethod
    async def count(self) -> int:
        """Return number of stored vectors."""

    @abstractmethod
    async def stats(self) -> VectorStoreStats:
        """Return vector store statistics."""

    @abstractmethod
    async def list_documents(self) -> list[str]:
        """Return list of document ids stored."""
