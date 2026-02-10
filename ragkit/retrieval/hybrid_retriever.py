"""Hybrid retriever combining semantic and lexical search."""

from __future__ import annotations

import asyncio

from ragkit.config.schema_v2 import RetrievalConfigV2
from ragkit.models import Chunk
from ragkit.retrieval.base_retriever import BaseRetriever, SearchResult
from ragkit.retrieval.lexical_retriever import LexicalRetriever
from ragkit.retrieval.semantic_retriever import SemanticRetriever
from ragkit.retrieval.utils.fusion import linear_fusion, reciprocal_rank_fusion


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining semantic and lexical search.

    Features:
    - Parallel execution of semantic and lexical search
    - Multiple fusion methods (RRF, linear, weighted_sum)
    - Alpha weighting for semantic/lexical balance
    - Score normalization
    """

    def __init__(
        self,
        semantic_retriever: SemanticRetriever,
        lexical_retriever: LexicalRetriever,
        config: RetrievalConfigV2,
    ):
        """Initialize hybrid retriever.

        Args:
            semantic_retriever: Semantic retriever instance
            lexical_retriever: Lexical retriever instance
            config: Retrieval configuration
        """
        self.semantic = semantic_retriever
        self.lexical = lexical_retriever
        self.config = config

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search using hybrid approach.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult, fused and sorted
        """
        # 1. Execute both retrievers in parallel
        # Fetch more results to allow for better fusion
        fetch_k = top_k * 2

        semantic_results, lexical_results = await asyncio.gather(
            self.semantic.search(query, fetch_k, filters),
            self.lexical.search(query, fetch_k, filters),
        )

        # 2. Fuse results based on configured method
        if self.config.fusion_method == "rrf":
            merged = reciprocal_rank_fusion(
                results_lists=[semantic_results, lexical_results],
                k=self.config.rrf_k,
            )
        elif self.config.fusion_method == "linear":
            merged = linear_fusion(
                semantic_results=semantic_results,
                lexical_results=lexical_results,
                alpha=self.config.alpha,
                normalize=self.config.normalize_scores,
                normalization_method=self.config.normalization_method,
            )
        elif self.config.fusion_method == "weighted_sum":
            # Use alpha to determine weights
            merged = linear_fusion(
                semantic_results=semantic_results,
                lexical_results=lexical_results,
                alpha=self.config.alpha,
                normalize=True,
                normalization_method=self.config.normalization_method,
            )
        elif self.config.fusion_method == "relative_score":
            merged = self._relative_score_fusion(semantic_results, lexical_results)
        else:
            raise ValueError(f"Unknown fusion method: {self.config.fusion_method}")

        # 3. Return top_k
        return merged[:top_k]

    def index_documents(self, chunks: list[Chunk]) -> None:
        """Index documents for both semantic and lexical search.

        Args:
            chunks: List of chunks to index
        """
        # Index in both retrievers
        self.semantic.index_documents(chunks)
        self.lexical.index_documents(chunks)

    def _relative_score_fusion(
        self,
        semantic_results: list[SearchResult],
        lexical_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Fuse using relative score normalization.

        Normalizes each list by its maximum score, then combines.

        Args:
            semantic_results: Semantic search results
            lexical_results: Lexical search results

        Returns:
            Merged results
        """
        # Normalize by max score in each list
        sem_scores = {r.chunk.id: r.score for r in semantic_results}
        lex_scores = {r.chunk.id: r.score for r in lexical_results}

        # Get max scores
        max_sem = max(sem_scores.values()) if sem_scores else 1.0
        max_lex = max(lex_scores.values()) if lex_scores else 1.0

        # Normalize
        sem_scores = {k: v / max_sem for k, v in sem_scores.items()}
        lex_scores = {k: v / max_lex for k, v in lex_scores.items()}

        # Combine
        all_ids = set(sem_scores.keys()) | set(lex_scores.keys())

        # Build doc map
        doc_map = {}
        for result in semantic_results + lexical_results:
            if result.chunk.id not in doc_map:
                doc_map[result.chunk.id] = result

        # Calculate combined scores
        merged = []
        for chunk_id in all_ids:
            sem_score = sem_scores.get(chunk_id, 0.0)
            lex_score = lex_scores.get(chunk_id, 0.0)

            # Weighted combination
            combined_score = (
                self.config.alpha * sem_score + (1 - self.config.alpha) * lex_score
            )

            merged.append(
                SearchResult(
                    chunk=doc_map[chunk_id].chunk,
                    score=combined_score,
                    metadata=doc_map[chunk_id].metadata,
                )
            )

        # Sort by combined score
        merged.sort(key=lambda x: x.score, reverse=True)

        return merged
