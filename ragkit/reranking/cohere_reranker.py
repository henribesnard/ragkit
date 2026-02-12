"""Cohere API-based reranker implementation."""

from __future__ import annotations

import logging
import time
from typing import Any

from ragkit.config.schema_v2 import RerankingConfigV2
from ragkit.models import Chunk
from ragkit.reranking.base_reranker import BaseReranker, RerankResult

logger = logging.getLogger(__name__)


class CohereReranker(BaseReranker):
    """Cohere Rerank API integration.

    Uses Cohere's rerank-v3.0 API for state-of-the-art reranking.
    This is a cloud-based solution that doesn't require local GPU.

    Features:
        - Best-in-class reranking quality (MRR@10 ~0.415)
        - No local compute required
        - Multilingual support (100+ languages)
        - Simple API integration

    Trade-offs:
        - Requires API key (paid service)
        - Network latency (~100-200ms)
        - Cost: $2 per 1000 searches (100 docs each)
        - Rate limits apply

    Cost analysis:
        - 10k queries/day × $0.002 = $20/day = $600/month
        - Best for: High-value applications, production RAG with budget

    Example:
        config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cohere-rerank-v3",
            rerank_top_n=100,
            final_top_k=5,
        )
        reranker = CohereReranker(config, api_key="your-key")
        results = await reranker.rerank(query, candidates)
    """

    def __init__(self, config: RerankingConfigV2, api_key: str) -> None:
        """Initialize Cohere reranker.

        Args:
            config: Reranking configuration
            api_key: Cohere API key

        Raises:
            ImportError: If cohere package not installed
        """
        self.config = config
        self.api_key = api_key

        try:
            import cohere
        except ImportError as exc:
            raise ImportError(
                "cohere package is required for Cohere reranking. Install with: pip install cohere"
            ) from exc

        self.client = cohere.Client(api_key)
        logger.info("Initialized Cohere reranker with API key")

    async def rerank(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """Rerank using Cohere Rerank API.

        Args:
            query: User query string
            chunks: List of candidate chunks from retrieval
            top_k: Number of results to return (defaults to config.final_top_k)

        Returns:
            List of RerankResult objects, sorted by relevance score

        Raises:
            ValueError: If inputs are invalid
            Exception: If API call fails
        """
        if top_k is None:
            top_k = self.config.final_top_k

        # Validate inputs
        self._validate_inputs(query, chunks, top_k)

        # Limit to rerank_top_n candidates
        candidates = chunks[: self.config.rerank_top_n]

        logger.debug(f"Calling Cohere Rerank API with {len(candidates)} documents")

        # Prepare documents for API
        docs_text = [chunk.content for chunk in candidates]

        # Call API with retry logic
        response = await self._call_api_with_retry(
            query=query,
            documents=docs_text,
            top_n=min(top_k, len(candidates)),
        )

        # Parse results
        results = []
        for rank, result in enumerate(response.results, start=1):
            # Get original chunk by index
            original_chunk = candidates[result.index]

            results.append(
                RerankResult(
                    chunk=original_chunk,
                    score=result.relevance_score,  # Normalized to [0, 1]
                    rank=rank,
                    metadata={
                        "api": "cohere",
                        "model": "rerank-v3.0",
                        "original_index": result.index,
                    },
                )
            )

        logger.info(f"Cohere reranking complete: {len(candidates)} → {len(results)} results")

        return results

    async def _call_api_with_retry(
        self,
        query: str,
        documents: list[str],
        top_n: int,
        max_retries: int = 3,
    ) -> Any:
        """Call Cohere API with exponential backoff retry.

        Args:
            query: Query string
            documents: List of document texts
            top_n: Number of results to return
            max_retries: Maximum number of retry attempts

        Returns:
            Cohere API response

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                response = self.client.rerank(
                    query=query,
                    documents=documents,
                    top_n=top_n,
                    model="rerank-english-v3.0",
                )
                return response

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Cohere API call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Cohere API call failed after {max_retries} attempts: {e}")
                    raise

    def estimate_cost(self, num_queries: int, docs_per_query: int = 100) -> dict:
        """Estimate Cohere API costs.

        Args:
            num_queries: Number of queries to estimate
            docs_per_query: Average documents per query

        Returns:
            Dictionary with cost breakdown
        """
        # Cohere pricing: ~$2 per 1000 searches (100 docs each)
        # Simplification: $0.002 per search
        cost_per_query = 0.002

        return {
            "num_queries": num_queries,
            "docs_per_query": docs_per_query,
            "cost_per_query_usd": cost_per_query,
            "total_cost_usd": num_queries * cost_per_query,
            "monthly_cost_usd": num_queries * cost_per_query * 30,
        }
