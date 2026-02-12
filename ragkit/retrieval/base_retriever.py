"""Base retriever interface for all retrieval strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from ragkit.models import Chunk


class SearchResult(BaseModel):
    """Result from a retrieval search."""

    chunk: Chunk
    score: float
    metadata: dict = {}


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects, sorted by relevance (highest score first)
        """
        pass

    @abstractmethod
    def index_documents(self, chunks: list[Chunk]) -> None:
        """Index documents for retrieval.

        Args:
            chunks: List of chunks to index
        """
        pass
