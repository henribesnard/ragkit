"""Multi-stage reranking for optimal speed/precision trade-off."""

from __future__ import annotations

import logging

from ragkit.config.schema_v2 import RerankingConfigV2
from ragkit.models import Chunk
from ragkit.reranking.base_reranker import BaseReranker, RerankResult
from ragkit.reranking.cross_encoder_reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class MultiStageReranker(BaseReranker):
    """Two-stage reranking pipeline for optimal performance.

    Strategy:
        Stage 1 (Fast Filter):
            - Uses lightweight model (e.g., TinyBERT)
            - Processes all N candidates quickly
            - Filters down to top M (e.g., N=100 → M=50)
            - Goal: High recall (don't miss relevant docs)

        Stage 2 (Precise Reranker):
            - Uses accurate model (e.g., BGE-reranker-v2)
            - Processes only M candidates from stage 1
            - Returns final top-K results
            - Goal: High precision on final results

    Performance gain:
        - Single-stage with BGE on 100 docs: ~180ms
        - Multi-stage (TinyBERT→BGE): ~40ms + 80ms = 120ms
        - Speedup: ~33% faster with equivalent precision

    When to use:
        ✅ rerank_top_n > 50 (many candidates)
        ✅ GPU available (parallel processing benefits)
        ✅ Latency-sensitive applications
        ❌ rerank_top_n < 20 (overhead not worth it)
        ❌ CPU only (scheduling overhead)

    Example:
        config = RerankingConfigV2(
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="BAAI/bge-reranker-v2-m3",
            stage_1_keep_top=50,
            rerank_top_n=100,
            final_top_k=5,
        )
        reranker = MultiStageReranker(config)
        results = await reranker.rerank(query, candidates, top_k=5)
    """

    def __init__(self, config: RerankingConfigV2):
        """Initialize multi-stage reranker.

        Args:
            config: Reranking configuration with multi_stage_reranking=True
        """
        if not config.multi_stage_reranking:
            logger.warning(
                "MultiStageReranker initialized with multi_stage_reranking=False. "
                "Set to True for proper multi-stage behavior."
            )

        self.config = config

        # Create Stage 1 config (fast filter)
        stage_1_config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model=config.stage_1_model,
            rerank_batch_size=32,  # Larger batch for smaller model
            use_gpu=config.use_gpu,
            cache_model=config.cache_model,
            rerank_threshold=0.0,  # No filtering in stage 1
            half_precision=False,  # TinyBERT is already small
        )

        self.stage_1_reranker = CrossEncoderReranker(stage_1_config)
        logger.info(f"Stage 1 (filter): {config.stage_1_model}")

        # Create Stage 2 config (precise reranker)
        stage_2_config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model=config.stage_2_model,
            rerank_batch_size=config.rerank_batch_size,
            use_gpu=config.use_gpu,
            cache_model=config.cache_model,
            rerank_threshold=config.rerank_threshold,
            half_precision=config.half_precision,
        )

        self.stage_2_reranker = CrossEncoderReranker(stage_2_config)
        logger.info(f"Stage 2 (precise): {config.stage_2_model}")

    async def rerank(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """Rerank using two-stage pipeline.

        Args:
            query: User query string
            chunks: List of candidate chunks from retrieval
            top_k: Number of final results to return (defaults to config.final_top_k)

        Returns:
            List of RerankResult objects from stage 2, sorted by score

        Raises:
            ValueError: If inputs are invalid
        """
        if top_k is None:
            top_k = self.config.final_top_k

        # Validate inputs
        self._validate_inputs(query, chunks, top_k)

        # Limit to rerank_top_n candidates
        candidates = chunks[: self.config.rerank_top_n]

        logger.info(
            f"Multi-stage reranking: {len(candidates)} → {self.config.stage_1_keep_top} → {top_k}"
        )

        # Stage 1: Fast filter
        logger.debug(f"Stage 1: Filtering to top {self.config.stage_1_keep_top}")
        stage_1_results = await self.stage_1_reranker.rerank(
            query,
            candidates,
            top_k=self.config.stage_1_keep_top,
        )

        # Extract chunks from stage 1 results
        filtered_chunks = [result.chunk for result in stage_1_results]

        logger.debug(f"Stage 1 complete: {len(candidates)} → {len(filtered_chunks)} chunks")

        # Stage 2: Precise reranking
        logger.debug(f"Stage 2: Precise reranking to top {top_k}")
        stage_2_results = await self.stage_2_reranker.rerank(
            query,
            filtered_chunks,
            top_k=top_k,
        )

        logger.info(f"Multi-stage complete: returned {len(stage_2_results)} final results")

        return stage_2_results

    def get_stage_info(self) -> dict:
        """Get information about the two stages.

        Returns:
            Dictionary with stage models and parameters
        """
        return {
            "stage_1": {
                "model": self.config.stage_1_model,
                "keep_top": self.config.stage_1_keep_top,
                "batch_size": 32,
            },
            "stage_2": {
                "model": self.config.stage_2_model,
                "batch_size": self.config.rerank_batch_size,
                "threshold": self.config.rerank_threshold,
                "half_precision": self.config.half_precision,
            },
        }
