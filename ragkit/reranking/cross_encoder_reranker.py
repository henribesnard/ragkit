"""Cross-encoder reranker implementation using HuggingFace models."""

from __future__ import annotations

import logging

from ragkit.config.schema_v2 import RerankingConfigV2
from ragkit.models import Chunk
from ragkit.reranking.base_reranker import BaseReranker, RerankResult

logger = logging.getLogger(__name__)


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder based reranker using sentence-transformers.

    Cross-encoders encode the query and document together, allowing for
    full attention between query and document tokens. This provides much
    better relevance scores than bi-encoders, at the cost of speed.

    Architecture:
        Input: "[CLS] query [SEP] document [SEP]"
        Output: Relevance score (typically in range [-10, 10])

    Features:
        - GPU acceleration (10-20x faster than CPU)
        - Batch processing for efficiency
        - Half-precision (FP16) to reduce VRAM usage
        - Model caching to avoid reloading
        - Configurable score thresholds

    Typical usage:
        1. Retrieval returns top-100 candidates
        2. Cross-encoder scores all 100 (query, doc) pairs
        3. Results re-sorted by cross-encoder scores
        4. Return top-5 most relevant

    Performance:
        - Latency: 50-200ms for 100 docs (GPU), 500-2000ms (CPU)
        - VRAM: 0.5-4GB depending on model size
        - Precision gain: +15-25% over retrieval alone
    """

    def __init__(self, config: RerankingConfigV2):
        """Initialize cross-encoder reranker.

        Args:
            config: Reranking configuration
        """
        self.config = config
        self.model = None
        self._device = None

    def _load_model(self):
        """Load cross-encoder model with optimizations.

        Lazy loading: model is loaded on first use, not at initialization.
        This avoids loading cost if reranking is disabled.

        Optimizations:
            - GPU usage if available and configured
            - Half-precision (FP16) on GPU to reduce VRAM
            - Model caching to avoid reloading between requests
        """
        # If model cached and caching enabled, skip reload
        if self.model is not None and self.config.cache_model:
            logger.debug("Using cached cross-encoder model")
            return

        logger.info(f"Loading cross-encoder model: {self.config.reranker_model}")

        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for cross-encoder reranking. "
                "Install with: pip install sentence-transformers"
            ) from exc

        # Determine device
        if self.config.use_gpu:
            try:
                import torch

                if torch.cuda.is_available():
                    self._device = "cuda"
                    logger.info("Using GPU for cross-encoder")
                else:
                    self._device = "cpu"
                    logger.warning("GPU requested but not available, using CPU")
            except ImportError:
                self._device = "cpu"
                logger.warning("PyTorch not available, using CPU")
        else:
            self._device = "cpu"
            logger.info("Using CPU for cross-encoder (use_gpu=False)")

        # Load model
        self.model = CrossEncoder(
            self.config.reranker_model,
            device=self._device,
            max_length=512,  # Truncate long documents
        )

        # Apply half-precision on GPU
        if self.config.half_precision and self._device == "cuda":
            try:
                self.model.model.half()
                logger.info("Using FP16 half-precision")
            except Exception as e:
                logger.warning(f"Failed to enable half-precision: {e}")

        logger.info(f"Model loaded successfully on {self._device}")

    async def rerank(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """Rerank chunks using cross-encoder scoring.

        Args:
            query: User query string
            chunks: List of candidate chunks from retrieval
            top_k: Number of top results to return (defaults to config.final_top_k)

        Returns:
            List of RerankResult objects, sorted by score (descending)

        Raises:
            ValueError: If inputs are invalid
        """
        # Use config default if top_k not specified
        if top_k is None:
            top_k = self.config.final_top_k

        # Validate inputs
        self._validate_inputs(query, chunks, top_k)

        # Limit candidates to rerank_top_n
        candidates = chunks[: self.config.rerank_top_n]

        if len(candidates) < len(chunks):
            logger.debug(
                f"Limiting reranking to top {self.config.rerank_top_n} candidates "
                f"(from {len(chunks)} total)"
            )

        # Load model (lazy loading)
        self._load_model()

        # Prepare (query, document) pairs
        pairs = [(query, chunk.content) for chunk in candidates]

        # Score all pairs in batches
        logger.debug(f"Scoring {len(pairs)} pairs with batch_size={self.config.rerank_batch_size}")

        try:
            scores = self.model.predict(
                pairs,
                batch_size=self.config.rerank_batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as e:
            logger.error(f"Cross-encoder scoring failed: {e}")
            raise

        # Convert scores to list if numpy array
        if hasattr(scores, "tolist"):
            scores = scores.tolist()

        # Combine chunks with scores
        scored_chunks = list(zip(candidates, scores, strict=False))

        # Filter by threshold
        if self.config.rerank_threshold > 0.0:
            before_filter = len(scored_chunks)
            scored_chunks = self._filter_by_threshold(scored_chunks, self.config.rerank_threshold)
            logger.debug(
                f"Filtered {before_filter - len(scored_chunks)} results below threshold "
                f"{self.config.rerank_threshold}"
            )

        # Sort by score (descending)
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Build final results
        results = self._build_results(scored_chunks, top_k)

        logger.info(f"Reranked {len(candidates)} candidates, returning top {len(results)}")

        return results

    def __del__(self):
        """Cleanup model on deletion if not caching."""
        if not self.config.cache_model and self.model is not None:
            logger.debug("Releasing cross-encoder model")
            del self.model
            self.model = None
