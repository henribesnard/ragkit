"""Tests for advanced embedding features."""

from __future__ import annotations

import numpy as np
import pytest

from ragkit.config.schema_v2 import EmbeddingConfigV2
from ragkit.embedding.advanced_embedder import AdvancedEmbedder


class TestEmbeddingCaching:
    """Tests for embedding cache."""

    @pytest.fixture
    def config(self):
        """Configuration with cache enabled."""
        return EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            cache_embeddings=True,
        )

    @pytest.mark.asyncio
    async def test_embedding_caching(self, config):
        """Verify that cache avoids re-computing embeddings."""
        embedder = AdvancedEmbedder(config)

        texts = ["This is a test.", "Another test."]

        # First call (without cache)
        embeddings_1 = await embedder.embed_batch(texts)

        # Verify cache is populated
        assert len(embedder.cache) == 2

        # Second call (with cache)
        embeddings_2 = await embedder.embed_batch(texts)

        # Embeddings must be identical (from cache)
        np.testing.assert_array_equal(embeddings_1, embeddings_2)

    @pytest.mark.asyncio
    async def test_cache_partial_hit(self, config):
        """Verify behavior with partial cache hit."""
        embedder = AdvancedEmbedder(config)

        # Embed 2 texts
        await embedder.embed_batch(["Text A", "Text B"])

        # Embed 3 texts: 2 cached, 1 new
        embeddings = await embedder.embed_batch([
            "Text A",  # Cache hit
            "Text C",  # Cache miss
            "Text B",  # Cache hit
        ])

        # Verify dimensions
        assert embeddings.shape == (3, 384)  # all-MiniLM-L6-v2 = 384 dims

        # Verify cache contains 3 entries
        assert len(embedder.cache) == 3


class TestRateLimiter:
    """Tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_rpm(self):
        """Verify that rate limiter respects RPM."""
        import time

        from ragkit.embedding.rate_limiter import RateLimiter

        # 3 requests per minute = 1 request every 20 seconds
        limiter = RateLimiter(rpm=3, tpm=None)

        start = time.time()

        # Make 4 requests
        for i in range(4):
            await limiter.acquire(tokens=100)

        elapsed = time.time() - start

        # First 3 pass instantly
        # 4th waits ~60 seconds (new minute start)
        # Tolerance of 5 seconds
        assert elapsed >= 55  # At least 55 seconds

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_tpm(self):
        """Verify that rate limiter respects TPM."""
        import time

        from ragkit.embedding.rate_limiter import RateLimiter

        # 1000 tokens per minute
        limiter = RateLimiter(rpm=None, tpm=1000)

        start = time.time()

        # Consume 500 tokens
        await limiter.acquire(tokens=500)

        # Consume 500 tokens (total 1000, OK)
        await limiter.acquire(tokens=500)

        # Consume 100 tokens (total 1100, exceeds => wait)
        await limiter.acquire(tokens=100)

        elapsed = time.time() - start

        # Must wait ~60 seconds before 3rd request
        assert elapsed >= 55


class TestDimensionalityReduction:
    """Tests for dimensionality reduction."""

    @pytest.mark.asyncio
    async def test_pca_reduction(self):
        """Verify that PCA reduction works."""
        config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",  # 384 dims
            dimensionality_reduction="pca",
            reduction_target_dims=128,
        )

        embedder = AdvancedEmbedder(config)

        texts = ["Test 1", "Test 2", "Test 3"]
        embeddings = await embedder.embed_batch(texts)

        # Verify dimensions
        assert embeddings.shape == (3, 128)  # Reduced from 384 to 128

    @pytest.mark.asyncio
    async def test_reduction_preserves_similarity_order(self):
        """Verify that reduction preserves similarity order."""
        config_full = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            dimensionality_reduction="none",
        )

        config_reduced = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            dimensionality_reduction="pca",
            reduction_target_dims=128,
        )

        embedder_full = AdvancedEmbedder(config_full)
        embedder_reduced = AdvancedEmbedder(config_reduced)

        texts = ["Python programming", "Java programming", "Cooking recipes"]

        # Full embeddings
        emb_full = await embedder_full.embed_batch(texts)

        # Reduced embeddings
        emb_reduced = await embedder_reduced.embed_batch(texts)

        # Full similarity
        sim_full_0_1 = np.dot(emb_full[0], emb_full[1])
        sim_full_0_2 = np.dot(emb_full[0], emb_full[2])

        # Reduced similarity
        sim_reduced_0_1 = np.dot(emb_reduced[0], emb_reduced[1])
        sim_reduced_0_2 = np.dot(emb_reduced[0], emb_reduced[2])

        # Similarity order must be preserved
        # Python-Java more similar than Python-Cooking
        assert sim_full_0_1 > sim_full_0_2
        assert sim_reduced_0_1 > sim_reduced_0_2


class TestQuantization:
    """Tests for quantization."""

    @pytest.mark.asyncio
    async def test_int8_quantization(self):
        """Verify that int8 quantization works."""
        config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            embedding_dtype="int8",
        )

        embedder = AdvancedEmbedder(config)

        texts = ["Test"]
        embeddings = await embedder.embed_batch(texts)

        # Verify dtype
        assert embeddings.dtype == np.int8

        # Verify value range
        assert embeddings.min() >= -127
        assert embeddings.max() <= 127
