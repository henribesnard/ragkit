"""Tests for cross-encoder reranker."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import RerankingConfigV2
from ragkit.models import Chunk
from ragkit.reranking.cross_encoder_reranker import CrossEncoderReranker


class TestCrossEncoderReranker:
    """Tests for cross-encoder based reranking."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_top_n=100,
            rerank_batch_size=16,
            rerank_threshold=0.0,
            final_top_k=5,
            use_gpu=False,  # Use CPU for tests
            cache_model=True,
        )

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            Chunk(
                id="1",
                content="Best practices for securing API endpoints include authentication",
                metadata={},
            ),
            Chunk(
                id="2",
                content="API security involves protecting endpoints from unauthorized access",
                metadata={},
            ),
            Chunk(
                id="3",
                content="Python programming for beginners tutorial",
                metadata={},
            ),
            Chunk(
                id="4",
                content="How to implement JWT authentication in REST APIs",
                metadata={},
            ),
            Chunk(
                id="5",
                content="Machine learning fundamentals and neural networks",
                metadata={},
            ),
        ]

    @pytest.mark.asyncio
    async def test_rerank_basic(self, config, sample_chunks):
        """Test basic reranking functionality."""
        reranker = CrossEncoderReranker(config)

        results = await reranker.rerank(
            query="How to secure API endpoints?",
            chunks=sample_chunks,
            top_k=3,
        )

        # Should return exactly 3 results
        assert len(results) == 3

        # Results should have ranks 1, 2, 3
        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3

        # Scores should be descending
        assert results[0].score >= results[1].score
        assert results[1].score >= results[2].score

    @pytest.mark.asyncio
    async def test_rerank_relevance(self, config, sample_chunks):
        """Test that reranking finds most relevant documents."""
        reranker = CrossEncoderReranker(config)

        results = await reranker.rerank(
            query="API security best practices",
            chunks=sample_chunks,
            top_k=3,
        )

        # Top results should be about API security (ids 1, 2, 4)
        top_ids = {r.chunk.id for r in results}

        # Should include at least 2 of the API security docs
        api_security_ids = {"1", "2", "4"}
        overlap = len(top_ids & api_security_ids)
        assert overlap >= 2, f"Expected API security docs in top results, got {top_ids}"

    @pytest.mark.asyncio
    async def test_score_threshold(self, sample_chunks):
        """Test score threshold filtering."""
        # High threshold to filter out low-relevance docs
        config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_top_n=100,
            rerank_threshold=2.0,  # High threshold
            final_top_k=10,
            use_gpu=False,
        )

        reranker = CrossEncoderReranker(config)

        results = await reranker.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=10,
        )

        # Should filter some results (threshold is high)
        # Exact number depends on model scores, but should be < 5
        assert len(results) <= 5

        # All results should meet threshold
        assert all(r.score >= 2.0 for r in results)

    @pytest.mark.asyncio
    async def test_batch_processing_consistency(self, config, sample_chunks):
        """Test that different batch sizes give same results."""
        # Batch size 1
        config_1 = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_batch_size=1,
            use_gpu=False,
            cache_model=False,  # Disable cache to ensure fresh computation
        )
        reranker_1 = CrossEncoderReranker(config_1)
        results_1 = await reranker_1.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=3,
        )

        # Batch size 8
        config_8 = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_batch_size=8,
            use_gpu=False,
            cache_model=False,
        )
        reranker_8 = CrossEncoderReranker(config_8)
        results_8 = await reranker_8.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=3,
        )

        # Should return same document IDs in same order
        ids_1 = [r.chunk.id for r in results_1]
        ids_8 = [r.chunk.id for r in results_8]
        assert ids_1 == ids_8

        # Scores should be very close (allowing small float differences)
        for r1, r8 in zip(results_1, results_8):
            assert abs(r1.score - r8.score) < 0.01

    @pytest.mark.asyncio
    async def test_top_k_limits_results(self, config, sample_chunks):
        """Test that top_k parameter limits results."""
        reranker = CrossEncoderReranker(config)

        # Request top 2
        results = await reranker.rerank(
            query="Python programming",
            chunks=sample_chunks,
            top_k=2,
        )

        assert len(results) == 2

        # Request top 10 (but only 5 chunks available)
        results = await reranker.rerank(
            query="Python programming",
            chunks=sample_chunks,
            top_k=10,
        )

        assert len(results) == 5  # Limited by available chunks

    @pytest.mark.asyncio
    async def test_rerank_top_n_limits_candidates(self, sample_chunks):
        """Test that rerank_top_n limits candidates processed."""
        # Create many chunks
        many_chunks = sample_chunks * 50  # 250 chunks

        config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_top_n=20,  # Only rerank top 20
            final_top_k=5,
            use_gpu=False,
        )

        reranker = CrossEncoderReranker(config)

        results = await reranker.rerank(
            query="API security",
            chunks=many_chunks,
            top_k=5,
        )

        # Should return 5 results
        assert len(results) == 5

        # Note: We can't directly verify only 20 were processed,
        # but the implementation should limit candidates


class TestCrossEncoderValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        config = RerankingConfigV2(use_gpu=False)
        reranker = CrossEncoderReranker(config)

        chunks = [Chunk(id="1", content="test", metadata={})]

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await reranker.rerank(query="", chunks=chunks)

    @pytest.mark.asyncio
    async def test_empty_chunks_raises(self):
        """Test that empty chunks list raises ValueError."""
        config = RerankingConfigV2(use_gpu=False)
        reranker = CrossEncoderReranker(config)

        with pytest.raises(ValueError, match="Chunks list cannot be empty"):
            await reranker.rerank(query="test query", chunks=[])

    @pytest.mark.asyncio
    async def test_invalid_top_k_raises(self):
        """Test that invalid top_k raises ValueError."""
        config = RerankingConfigV2(use_gpu=False)
        reranker = CrossEncoderReranker(config)

        chunks = [Chunk(id="1", content="test", metadata={})]

        with pytest.raises(ValueError, match="top_k must be >= 1"):
            await reranker.rerank(query="test", chunks=chunks, top_k=0)


class TestModelCaching:
    """Tests for model caching behavior."""

    @pytest.mark.asyncio
    async def test_model_cached_between_calls(self):
        """Test that model is cached when cache_model=True."""
        config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            use_gpu=False,
            cache_model=True,
        )

        reranker = CrossEncoderReranker(config)

        chunks = [Chunk(id="1", content="test document", metadata={})]

        # First call - loads model
        await reranker.rerank(query="test", chunks=chunks)
        assert reranker.model is not None
        model_ref = reranker.model

        # Second call - should reuse cached model
        await reranker.rerank(query="test", chunks=chunks)
        assert reranker.model is model_ref  # Same object

    @pytest.mark.asyncio
    async def test_model_not_loaded_initially(self):
        """Test lazy loading - model not loaded at init."""
        config = RerankingConfigV2(use_gpu=False)
        reranker = CrossEncoderReranker(config)

        # Model should be None before first use
        assert reranker.model is None
