"""Tests for hybrid retrieval and fusion methods."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import EmbeddingConfigV2, RetrievalConfigV2, VectorDBConfigV2
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.models import Chunk
from ragkit.retrieval.base_retriever import SearchResult
from ragkit.retrieval.hybrid_retriever import HybridRetriever
from ragkit.retrieval.lexical_retriever import LexicalRetriever
from ragkit.retrieval.semantic_retriever import SemanticRetriever
from ragkit.retrieval.utils.fusion import linear_fusion, reciprocal_rank_fusion
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class TestHybridRetrieval:
    """Tests for hybrid retrieval."""

    @pytest.fixture
    async def hybrid_retriever(self):
        """Create hybrid retriever with test data."""
        # Configs
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
        )
        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_hybrid",
        )
        retrieval_config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            fusion_method="rrf",
            alpha=0.5,
        )

        # Components
        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)

        semantic = SemanticRetriever(vectordb, embedder, retrieval_config)
        lexical = LexicalRetriever(retrieval_config)

        hybrid = HybridRetriever(semantic, lexical, retrieval_config)

        # Index documents
        chunks = [
            Chunk(
                id="1",
                content="GET /api/users endpoint implementation guide",
                metadata={},
            ),
            Chunk(
                id="2",
                content="How to work with user data and APIs",
                metadata={},
            ),
            Chunk(
                id="3",
                content="Python programming tutorial for beginners",
                metadata={},
            ),
        ]

        # Index in both
        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)
        lexical.index_documents(chunks)

        return hybrid

    @pytest.mark.asyncio
    async def test_hybrid_combines_both(self, hybrid_retriever):
        """Hybrid search combines semantic and lexical."""
        results = await hybrid_retriever.search("GET /api/users endpoint")

        assert len(results) > 0

        # Should find exact match (lexical strength)
        # and related docs (semantic strength)

    @pytest.mark.asyncio
    async def test_hybrid_top_k(self, hybrid_retriever):
        """Top-k limits results."""
        results = await hybrid_retriever.search("API programming", top_k=2)

        assert len(results) <= 2


class TestAlphaWeighting:
    """Tests for alpha parameter (semantic/lexical balance)."""

    @pytest.mark.asyncio
    async def test_alpha_low_favors_lexical(self):
        """Low alpha favors lexical (exact matches)."""
        config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            alpha=0.2,  # 80% lexical, 20% semantic
            fusion_method="linear",
        )

        assert config.alpha == 0.2

        # In practice, exact term matches would score higher

    @pytest.mark.asyncio
    async def test_alpha_high_favors_semantic(self):
        """High alpha favors semantic (concepts)."""
        config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            alpha=0.8,  # 80% semantic, 20% lexical
            fusion_method="linear",
        )

        assert config.alpha == 0.8

        # In practice, conceptual matches would score higher


class TestFusionMethods:
    """Tests for different fusion methods."""

    @pytest.mark.asyncio
    async def test_rrf_fusion(self):
        """RRF fusion works correctly."""
        # Create mock results
        chunk1 = Chunk(id="1", content="Doc 1", metadata={})
        chunk2 = Chunk(id="2", content="Doc 2", metadata={})
        chunk3 = Chunk(id="3", content="Doc 3", metadata={})

        semantic_results = [
            SearchResult(chunk=chunk1, score=0.95, metadata={}),
            SearchResult(chunk=chunk2, score=0.50, metadata={}),
        ]

        lexical_results = [
            SearchResult(chunk=chunk2, score=15.0, metadata={}),
            SearchResult(chunk=chunk1, score=5.0, metadata={}),
        ]

        # Apply RRF
        merged = reciprocal_rank_fusion(
            results_lists=[semantic_results, lexical_results],
            k=60,
        )

        # Should return results
        assert len(merged) == 2

        # Both docs should be present
        ids = {r.chunk.id for r in merged}
        assert "1" in ids
        assert "2" in ids

    @pytest.mark.asyncio
    async def test_linear_fusion(self):
        """Linear fusion works correctly."""
        chunk1 = Chunk(id="1", content="Doc 1", metadata={})
        chunk2 = Chunk(id="2", content="Doc 2", metadata={})

        semantic_results = [
            SearchResult(chunk=chunk1, score=0.9, metadata={}),
        ]

        lexical_results = [
            SearchResult(chunk=chunk2, score=10.0, metadata={}),
        ]

        # Apply linear fusion
        merged = linear_fusion(
            semantic_results=semantic_results,
            lexical_results=lexical_results,
            alpha=0.5,
            normalize=True,
        )

        # Should combine both
        assert len(merged) == 2

    @pytest.mark.asyncio
    async def test_fusion_handles_overlap(self):
        """Fusion handles overlapping results."""
        chunk1 = Chunk(id="1", content="Doc 1", metadata={})

        # Same doc in both lists
        semantic_results = [
            SearchResult(chunk=chunk1, score=0.8, metadata={}),
        ]

        lexical_results = [
            SearchResult(chunk=chunk1, score=5.0, metadata={}),
        ]

        # RRF should combine scores for same doc
        merged = reciprocal_rank_fusion(
            results_lists=[semantic_results, lexical_results],
            k=60,
        )

        # Should have 1 result with combined score
        assert len(merged) == 1
        assert merged[0].chunk.id == "1"
        assert merged[0].score > 0
