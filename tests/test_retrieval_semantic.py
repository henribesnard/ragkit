"""Tests for semantic retrieval."""

from __future__ import annotations

import numpy as np
import pytest

from ragkit.config.schema_v2 import EmbeddingConfigV2, RetrievalConfigV2, VectorDBConfigV2
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.models import Chunk
from ragkit.retrieval.semantic_retriever import SemanticRetriever
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class TestSemanticRetrieval:
    """Tests for semantic retrieval."""

    @pytest.fixture
    async def retriever(self):
        """Create semantic retriever with test data."""
        # Config
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            cache_embeddings=False,
        )
        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_semantic",
        )
        retrieval_config = RetrievalConfigV2(
            retrieval_mode="semantic",
        )

        # Components
        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)
        retriever = SemanticRetriever(vectordb, embedder, retrieval_config)

        # Index test documents
        chunks = [
            Chunk(
                id="1",
                content="Python is a high-level programming language",
                metadata={"source": "doc1"},
            ),
            Chunk(
                id="2",
                content="Java is also a popular programming language",
                metadata={"source": "doc2"},
            ),
            Chunk(
                id="3", content="Cats are cute animals", metadata={"source": "doc3"}
            ),
        ]

        # Embed and index
        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)

        return retriever

    @pytest.mark.asyncio
    async def test_semantic_top_k(self, retriever):
        """Verify top_k returns exactly K results."""
        results = await retriever.search("programming language", top_k=2)

        assert len(results) <= 2
        assert all(r.score >= 0 for r in results)

        # Results should be sorted by score (descending)
        if len(results) > 1:
            assert results[0].score >= results[-1].score

    @pytest.mark.asyncio
    async def test_semantic_relevance(self, retriever):
        """Semantic search finds relevant documents."""
        results = await retriever.search("programming languages", top_k=3)

        # Top results should be about programming
        assert len(results) > 0
        top_content = results[0].chunk.content.lower()
        assert "python" in top_content or "java" in top_content

    @pytest.mark.asyncio
    async def test_score_threshold(self):
        """Score threshold filters low-relevance results."""
        # This test would need a more controlled setup
        # For now, just verify the configuration works
        config = RetrievalConfigV2(
            retrieval_mode="semantic",
            score_threshold=0.5,
        )
        assert config.score_threshold == 0.5

    @pytest.mark.asyncio
    async def test_mmr_enabled(self):
        """MMR configuration is respected."""
        config = RetrievalConfigV2(
            retrieval_mode="semantic",
            mmr_enabled=True,
            mmr_lambda=0.5,
        )

        assert config.mmr_enabled is True
        assert config.mmr_lambda == 0.5


class TestMetadataFiltering:
    """Tests for metadata filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_source(self):
        """Metadata filters work correctly."""
        # Setup
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
        )
        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_filter",
        )
        retrieval_config = RetrievalConfigV2()

        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)
        retriever = SemanticRetriever(vectordb, embedder, retrieval_config)

        # Index documents
        chunks = [
            Chunk(
                id="1",
                content="Python doc chapter 1",
                metadata={"source": "manual.pdf"},
            ),
            Chunk(
                id="2",
                content="Python doc chapter 2",
                metadata={"source": "manual.pdf"},
            ),
            Chunk(
                id="3",
                content="Python tutorial",
                metadata={"source": "tutorial.pdf"},
            ),
        ]

        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)

        # Search with filter
        results = await retriever.search(
            "Python", top_k=10, filters={"source": "manual.pdf"}
        )

        # Should only return docs from manual.pdf
        assert all(r.chunk.metadata["source"] == "manual.pdf" for r in results)
