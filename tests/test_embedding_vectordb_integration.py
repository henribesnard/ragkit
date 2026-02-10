"""Integration tests for embedding and vector DB pipeline."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import ChunkingConfigV2, EmbeddingConfigV2, VectorDBConfigV2
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.ingestion.chunkers.factory import create_chunker
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class TestCompletePipeline:
    """Integration tests for complete RAG pipeline."""

    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return ParsedDocument(
            content=(
                "Introduction to Python. "
                "Python is a high-level programming language. "
                "It was created by Guido van Rossum in 1991. "
                "\n\n"
                "Python Features. "
                "Python supports multiple programming paradigms. "
                "It has a dynamic type system and automatic memory management. "
                "\n\n"
                "Python Applications. "
                "Python is widely used in web development, data science, and automation. "
                "Popular frameworks include Django and Flask. "
            ),
            metadata={"title": "Python Guide", "author": "Test"},
        )

    @pytest.mark.asyncio
    async def test_chunk_embed_insert_search(self, sample_document):
        """Test complete pipeline: chunk -> embed -> insert -> search."""
        # Step 1: Chunking
        chunking_config = ChunkingConfigV2(
            strategy="fixed_size", chunk_size=100, chunk_overlap=20
        )
        chunker = create_chunker("fixed_size", chunk_size=100, chunk_overlap=20)
        chunks = await chunker.chunk_async(sample_document)

        assert len(chunks) > 0

        # Step 2: Embedding
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            cache_embeddings=True,
        )
        embedder = AdvancedEmbedder(embedding_config)

        # Extract chunk contents
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await embedder.embed_batch(chunk_texts)

        assert embeddings.shape[0] == len(chunks)
        assert embeddings.shape[1] == 384  # all-MiniLM-L6-v2 dimensions

        # Step 3: Vector DB insertion
        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_integration",
        )
        adapter = ChromaDBAdapter(vectordb_config)

        await adapter.insert_batch(chunks, embeddings)

        # Step 4: Search
        query = "What is Python?"
        query_embedding = await embedder.embed_query(query)

        results = await adapter.search(query_embedding, top_k=5)

        # Verify results
        assert len(results) > 0
        assert len(results) <= 5

        # Top result should be about Python
        top_chunk, top_score = results[0]
        assert "Python" in top_chunk.content

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, sample_document):
        """Test that cache reduces embedding time."""
        import time

        # Create embedder with cache
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            cache_embeddings=True,
        )
        embedder = AdvancedEmbedder(embedding_config)

        texts = ["Test text 1", "Test text 2", "Test text 3"]

        # First call (no cache)
        start = time.time()
        embeddings_1 = await embedder.embed_batch(texts)
        time_no_cache = time.time() - start

        # Second call (with cache)
        start = time.time()
        embeddings_2 = await embedder.embed_batch(texts)
        time_with_cache = time.time() - start

        # With cache should be much faster (at least 10x)
        assert time_with_cache < time_no_cache / 10

        # Embeddings should be identical
        import numpy as np

        np.testing.assert_array_equal(embeddings_1, embeddings_2)

    @pytest.mark.asyncio
    async def test_search_with_metadata_filters(self):
        """Test search with metadata filters."""
        from ragkit.models import Chunk

        # Create chunks with different sources
        chunks = [
            Chunk(
                content="Python documentation chapter 1",
                metadata={"source": "manual.pdf", "chapter": 1},
            ),
            Chunk(
                content="Python documentation chapter 2",
                metadata={"source": "manual.pdf", "chapter": 2},
            ),
            Chunk(
                content="Python tutorial introduction",
                metadata={"source": "tutorial.pdf", "chapter": 1},
            ),
        ]

        # Embed
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers", model="all-MiniLM-L6-v2"
        )
        embedder = AdvancedEmbedder(embedding_config)

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await embedder.embed_batch(chunk_texts)

        # Insert into VectorDB
        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_filters",
        )
        adapter = ChromaDBAdapter(vectordb_config)

        await adapter.insert_batch(chunks, embeddings)

        # Search with filter
        query = "Python documentation"
        query_embedding = await embedder.embed_query(query)

        results = await adapter.search(
            query_embedding, top_k=10, filters={"source": "manual.pdf"}
        )

        # Should only return chunks from manual.pdf
        assert len(results) == 2
        for chunk, score in results:
            assert chunk.metadata["source"] == "manual.pdf"

    @pytest.mark.asyncio
    async def test_parent_child_chunking_with_embedding(self):
        """Test parent-child chunking strategy with embeddings."""
        document = ParsedDocument(
            content="This is a test sentence. " * 200,  # Long document
            metadata={"title": "Test Doc"},
        )

        # Use parent-child chunking
        chunking_config = ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=1000,
            child_chunk_size=300,
        )
        chunker = create_chunker(
            "parent_child", parent_chunk_size=1000, child_chunk_size=300
        )

        chunks = await chunker.chunk_async(document)

        # Verify parent-child structure
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"
            assert "parent_content" in chunk.metadata

        # Embed child chunks
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers", model="all-MiniLM-L6-v2"
        )
        embedder = AdvancedEmbedder(embedding_config)

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await embedder.embed_batch(chunk_texts)

        # Verify embeddings
        assert embeddings.shape[0] == len(chunks)

        # In a real system, when retrieving, we would:
        # 1. Search on child embeddings (precise retrieval)
        # 2. Return parent content (extended context for LLM)
        # Here we just verify the structure exists
        for chunk in chunks:
            parent_content = chunk.metadata["parent_content"]
            assert len(parent_content) > len(chunk.content)
