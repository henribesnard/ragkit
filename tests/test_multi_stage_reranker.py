"""Tests for multi-stage reranker."""

from __future__ import annotations

import pytest

pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")

from ragkit.config.schema_v2 import RerankingConfigV2
from ragkit.models import Chunk
from ragkit.reranking.multi_stage_reranker import MultiStageReranker


class TestMultiStageReranker:
    """Tests for two-stage reranking pipeline."""

    @pytest.fixture
    def config(self):
        """Create multi-stage configuration."""
        return RerankingConfigV2(
            reranker_enabled=True,
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            stage_1_keep_top=10,
            rerank_top_n=20,
            final_top_k=5,
            use_gpu=False,  # Use CPU for tests
            cache_model=True,
        )

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        chunks = []
        # Add 20 API-related docs
        for i in range(10):
            chunks.append(
                Chunk(
                    id=f"api_{i}",
                    content=f"API security and authentication best practices {i}",
                    metadata={},
                )
            )

        # Add 10 unrelated docs
        for i in range(10):
            chunks.append(
                Chunk(
                    id=f"other_{i}",
                    content=f"Python programming tutorial for beginners {i}",
                    metadata={},
                )
            )

        return chunks

    @pytest.mark.asyncio
    async def test_multi_stage_basic(self, config, sample_chunks):
        """Test basic multi-stage reranking."""
        reranker = MultiStageReranker(config)

        results = await reranker.rerank(
            query="How to secure API endpoints?",
            chunks=sample_chunks,
            top_k=5,
        )

        # Should return 5 results
        assert len(results) == 5

        # Results should have ranks 1-5
        assert [r.rank for r in results] == [1, 2, 3, 4, 5]

        # Scores should be descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_stage_1_filters_correctly(self, config, sample_chunks):
        """Test that stage 1 filters down to stage_1_keep_top."""
        reranker = MultiStageReranker(config)

        # 20 candidates → stage 1 filters to 10 → stage 2 picks top 5
        results = await reranker.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=5,
        )

        assert len(results) == 5

        # Results should be mostly API-related (stage 1 filtered well)
        api_count = sum(1 for r in results if r.chunk.id.startswith("api_"))
        assert api_count >= 4, "Stage 1 should filter to API-related docs"

    @pytest.mark.asyncio
    async def test_get_stage_info(self, config):
        """Test get_stage_info returns correct configuration."""
        reranker = MultiStageReranker(config)

        info = reranker.get_stage_info()

        assert info["stage_1"]["model"] == "cross-encoder/ms-marco-TinyBERT-L-2-v2"
        assert info["stage_1"]["keep_top"] == 10

        assert info["stage_2"]["model"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert info["stage_2"]["batch_size"] == config.rerank_batch_size

    @pytest.mark.asyncio
    async def test_multi_stage_with_few_candidates(self, config):
        """Test multi-stage with fewer candidates than stage_1_keep_top."""
        # Only 5 chunks, but stage_1_keep_top=10
        few_chunks = [Chunk(id=f"{i}", content=f"document {i}", metadata={}) for i in range(5)]

        reranker = MultiStageReranker(config)

        results = await reranker.rerank(
            query="test query",
            chunks=few_chunks,
            top_k=3,
        )

        # Should return 3 results (limited by top_k)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_multi_stage_respects_top_k(self, config, sample_chunks):
        """Test that final top_k is respected."""
        reranker = MultiStageReranker(config)

        # Request different top_k values
        results_3 = await reranker.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=3,
        )
        assert len(results_3) == 3

        results_7 = await reranker.rerank(
            query="API security",
            chunks=sample_chunks,
            top_k=7,
        )
        assert len(results_7) == 7


class TestMultiStageConfiguration:
    """Tests for multi-stage configuration validation."""

    @pytest.mark.asyncio
    async def test_warning_if_multi_stage_false(self):
        """Test warning logged if multi_stage_reranking=False."""
        config = RerankingConfigV2(
            multi_stage_reranking=False,  # Incorrect for MultiStageReranker
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            use_gpu=False,
        )

        # Should still work but log warning
        reranker = MultiStageReranker(config)
        assert reranker is not None

    @pytest.mark.asyncio
    async def test_different_stage_models(self):
        """Test that different models can be configured for each stage."""
        config = RerankingConfigV2(
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="BAAI/bge-reranker-v2-m3",
            stage_1_keep_top=20,
            use_gpu=False,
        )

        reranker = MultiStageReranker(config)

        # Verify models are different
        assert (
            reranker.stage_1_reranker.config.reranker_model
            != reranker.stage_2_reranker.config.reranker_model
        )


class TestMultiStageVsSingleStage:
    """Tests comparing multi-stage to single-stage reranking."""

    @pytest.mark.asyncio
    async def test_multi_stage_results_similar_to_single_stage(self):
        """Test that multi-stage gives similar results to single-stage."""
        chunks = [
            Chunk(
                id="1",
                content="Best practices for API security and authentication",
                metadata={},
            ),
            Chunk(
                id="2",
                content="How to protect API endpoints from attacks",
                metadata={},
            ),
            Chunk(
                id="3",
                content="Python tutorial for beginners",
                metadata={},
            ),
            Chunk(
                id="4",
                content="Machine learning with neural networks",
                metadata={},
            ),
        ]

        query = "API security best practices"

        # Multi-stage
        multi_config = RerankingConfigV2(
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            stage_1_keep_top=4,
            use_gpu=False,
        )
        multi_reranker = MultiStageReranker(multi_config)
        multi_results = await multi_reranker.rerank(query, chunks, top_k=2)

        # Single-stage (directly with stage 2 model)
        from ragkit.reranking.cross_encoder_reranker import CrossEncoderReranker

        single_config = RerankingConfigV2(
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            use_gpu=False,
        )
        single_reranker = CrossEncoderReranker(single_config)
        single_results = await single_reranker.rerank(query, chunks, top_k=2)

        # Top results should be same (or very similar)
        multi_ids = [r.chunk.id for r in multi_results]
        single_ids = [r.chunk.id for r in single_results]

        # At least top-1 should match
        assert multi_ids[0] == single_ids[0]


class TestStageParameters:
    """Tests for stage-specific parameters."""

    @pytest.mark.asyncio
    async def test_stage_1_larger_batch_size(self):
        """Test that stage 1 uses larger batch size (optimization)."""
        config = RerankingConfigV2(
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_batch_size=16,  # Stage 2 batch size
            use_gpu=False,
        )

        reranker = MultiStageReranker(config)

        # Stage 1 should use batch_size=32 (hardcoded optimization)
        info = reranker.get_stage_info()
        assert info["stage_1"]["batch_size"] == 32
        assert info["stage_2"]["batch_size"] == 16

    @pytest.mark.asyncio
    async def test_stage_2_respects_threshold(self):
        """Test that stage 2 applies rerank_threshold."""
        config = RerankingConfigV2(
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_threshold=1.0,  # Only stage 2 should apply this
            use_gpu=False,
        )

        reranker = MultiStageReranker(config)

        # Verify stage configurations
        assert reranker.stage_1_reranker.config.rerank_threshold == 0.0  # No threshold
        assert reranker.stage_2_reranker.config.rerank_threshold == 1.0  # Threshold applied
