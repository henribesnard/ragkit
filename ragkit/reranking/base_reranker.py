"""Base reranker interface for all reranking implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ragkit.models import Chunk


@dataclass
class RerankResult:
    """Result from reranking operation.

    Attributes:
        chunk: The document chunk
        score: Reranking score (typically in range [-10, 10] for cross-encoders)
        rank: Position after reranking (1-indexed)
        metadata: Additional metadata about the reranking
    """

    chunk: Chunk
    score: float
    rank: int
    metadata: dict = field(default_factory=dict)


class BaseReranker(ABC):
    """Abstract base class for all rerankers.

    Rerankers take a query and a list of candidate documents (from retrieval)
    and reorder them based on fine-grained relevance scoring.

    Typical workflow:
        1. Retrieval system returns top-N candidates (e.g., N=100)
        2. Reranker scores each (query, document) pair
        3. Results are re-sorted by reranker scores
        4. Top-K final results returned (e.g., K=5)

    Implementations:
        - CrossEncoderReranker: Uses transformer cross-encoders (precise but slow)
        - MultiStageReranker: Two-stage pipeline (fast filter → precise rerank)
        - CohereReranker: API-based reranking via Cohere
        - LLMReranker: Uses LLM as judge (very slow but flexible)
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank documents by relevance to query.

        Args:
            query: User query string
            chunks: List of candidate chunks (already filtered by retrieval)
            top_k: Number of top results to return after reranking

        Returns:
            List of RerankResult objects, sorted by score (descending)

        Raises:
            ValueError: If chunks is empty or top_k < 1
        """
        pass

    def _validate_inputs(self, query: str, chunks: list[Chunk], top_k: int):
        """Validate reranking inputs.

        Args:
            query: User query string
            chunks: List of candidate chunks
            top_k: Number of results to return

        Raises:
            ValueError: If inputs are invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")

    def _filter_by_threshold(
        self,
        results: list[tuple[Chunk, float]],
        threshold: float,
    ) -> list[tuple[Chunk, float]]:
        """Filter results below score threshold.

        Args:
            results: List of (chunk, score) tuples
            threshold: Minimum score to keep

        Returns:
            Filtered list of (chunk, score) tuples
        """
        return [(chunk, score) for chunk, score in results if score >= threshold]

    def _build_results(
        self,
        scored_chunks: list[tuple[Chunk, float]],
        top_k: int,
    ) -> list[RerankResult]:
        """Build final RerankResult objects from scored chunks.

        Args:
            scored_chunks: List of (chunk, score) tuples, pre-sorted
            top_k: Number of results to return

        Returns:
            List of RerankResult objects with ranks assigned
        """
        results = []
        for rank, (chunk, score) in enumerate(scored_chunks[:top_k], start=1):
            results.append(
                RerankResult(
                    chunk=chunk,
                    score=score,
                    rank=rank,
                    metadata={},
                )
            )
        return results
