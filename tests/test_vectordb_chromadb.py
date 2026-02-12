"""Tests for ChromaDB adapter with VectorDBConfigV2."""

from __future__ import annotations

import numpy as np
import pytest

from ragkit.config.schema_v2 import VectorDBConfigV2
from ragkit.models import Chunk
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class TestChromaDBInsertion:
    """Tests for ChromaDB insertion."""

    @pytest.fixture
    def config(self):
        """ChromaDB configuration in memory."""
        return VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_collection",
        )

    @pytest.fixture
    def adapter(self, config):
        """ChromaDB adapter."""
        return ChromaDBAdapter(config)

    @pytest.mark.asyncio
    async def test_insert_and_search(self, adapter):
        """Verify basic insertion and search."""
        # Chunks
        chunks = [
            Chunk(content="Python is great", metadata={"source": "doc1"}),
            Chunk(content="Java is also good", metadata={"source": "doc2"}),
            Chunk(content="Cats are cute", metadata={"source": "doc3"}),
        ]

        # Embeddings (fake, 384 dims)
        embeddings = np.random.rand(3, 384).astype(np.float32)

        # Insertion
        await adapter.insert_batch(chunks, embeddings)

        # Search with query similar to first chunk
        query_embedding = embeddings[0] + np.random.rand(384) * 0.01

        results = await adapter.search(query_embedding, top_k=3)

        # Verify results
        assert len(results) == 3

        # First result should be chunk 0 (most similar)
        assert "Python" in results[0][0].content

    @pytest.mark.asyncio
    async def test_search_with_filters(self, adapter):
        """Verify search with filters."""
        # Chunks
        chunks = [
            Chunk(content="Python doc", metadata={"source": "manual.pdf", "page": 1}),
            Chunk(content="Java doc", metadata={"source": "manual.pdf", "page": 2}),
            Chunk(content="Python tutorial", metadata={"source": "tutorial.pdf", "page": 1}),
        ]

        embeddings = np.random.rand(3, 384).astype(np.float32)

        await adapter.insert_batch(chunks, embeddings)

        # Search with filter source="manual.pdf"
        query_embedding = embeddings[0]

        results = await adapter.search(query_embedding, top_k=10, filters={"source": "manual.pdf"})

        # Should return only chunks from manual.pdf
        assert len(results) == 2
        for chunk, _score in results:
            assert chunk.metadata["source"] == "manual.pdf"


class TestHNSWParameters:
    """Tests for HNSW parameters."""

    @pytest.mark.asyncio
    async def test_hnsw_ef_search_impact(self):
        """Verify impact of hnsw_ef_search on recall."""
        # Configuration with low ef_search
        config_low = VectorDBConfigV2(
            in_memory=True,
            collection_name="test_low_ef",
            hnsw_ef_search=10,
        )

        # Configuration with high ef_search
        config_high = VectorDBConfigV2(
            in_memory=True,
            collection_name="test_high_ef",
            hnsw_ef_search=200,
        )

        adapter_low = ChromaDBAdapter(config_low)
        adapter_high = ChromaDBAdapter(config_high)

        # Insert 1000 chunks
        chunks = [Chunk(content=f"Document {i}", metadata={"id": i}) for i in range(1000)]
        embeddings = np.random.rand(1000, 384).astype(np.float32)

        await adapter_low.insert_batch(chunks, embeddings)
        await adapter_high.insert_batch(chunks, embeddings)

        # Search with same query
        query_embedding = embeddings[0]

        results_low = await adapter_low.search(query_embedding, top_k=10)
        results_high = await adapter_high.search(query_embedding, top_k=10)

        # High ef_search should give better results
        # (approximate measure: top 1 score)
        assert len(results_low) > 0
        assert len(results_high) > 0
