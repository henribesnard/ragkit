"""Tests for parent-child chunking."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.parent_child import ParentChildChunker
from ragkit.ingestion.parsers.base import ParsedDocument


class TestParentChildChunking:
    """Tests for the parent-child chunker."""

    @pytest.fixture
    def config(self):
        """Default configuration."""
        return ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=1000,
            child_chunk_size=300,
            parent_child_overlap=50,
        )

    @pytest.mark.asyncio
    async def test_creates_parent_child_relationship(self, config):
        """Test creation of parent-child relationship."""
        chunker = ParentChildChunker(config)

        # Long document (>1000 tokens)
        text = "This is a test sentence. " * 200  # ~1000 tokens
        document = ParsedDocument(content=text, metadata={"title": "Test Doc"})

        chunks = await chunker.chunk_async(document)

        # Verify structure
        assert len(chunks) > 0

        # All returned chunks are children
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"
            assert "parent_id" in chunk.metadata
            assert "parent_content" in chunk.metadata

            # Parent must be larger than child
            assert len(chunk.metadata["parent_content"]) > len(chunk.content)

    @pytest.mark.asyncio
    async def test_parent_provides_context(self, config):
        """Test that parent provides context."""
        chunker = ParentChildChunker(config)

        # Document with distinct sections
        section1 = (
            "Introduction to AI. Artificial Intelligence is a field of computer science. " * 50
        )
        section2 = "Machine Learning basics. ML is a subset of AI. " * 50

        text = section1 + section2
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Verify each child has access to parent context
        for chunk in chunks:
            parent_content = chunk.metadata["parent_content"]

            # Parent contains child AND additional context
            assert chunk.content in parent_content
            assert len(parent_content) >= len(chunk.content)

    @pytest.mark.asyncio
    async def test_child_index_in_parent(self, config):
        """Test that children are properly indexed within their parent."""
        chunker = ParentChildChunker(config)

        text = "Test. " * 500  # ~500 tokens
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Verify each child knows its position
        for chunk in chunks:
            assert "child_index_in_parent" in chunk.metadata
            assert "total_children_in_parent" in chunk.metadata

            # Index must be < total
            assert (
                chunk.metadata["child_index_in_parent"] < chunk.metadata["total_children_in_parent"]
            )

    @pytest.mark.asyncio
    async def test_metadata_inheritance(self, config):
        """Test that document metadata is inherited."""
        chunker = ParentChildChunker(config)

        document = ParsedDocument(
            content="Test. " * 500, metadata={"title": "My Document", "author": "John Doe"}
        )

        chunks = await chunker.chunk_async(document)

        # Document metadata should be copied
        for chunk in chunks:
            assert chunk.metadata["document_title"] == "My Document"

    @pytest.mark.asyncio
    async def test_sync_chunk_method(self, config):
        """Test sync chunk method."""
        chunker = ParentChildChunker(config)

        text = "Short test document. " * 100
        document = ParsedDocument(content=text, metadata={})

        # Call sync method
        chunks = chunker.chunk(document)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"


class TestParentChildChunkingEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_short_document(self):
        """Test document shorter than a parent chunk."""
        config = ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=1000,
            child_chunk_size=300,
        )

        chunker = ParentChildChunker(config)

        # Short document (100 tokens)
        text = "Short document. " * 20
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Should create at least 1 child chunk
        assert len(chunks) >= 1

        # All must have a parent
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"
            assert "parent_content" in chunk.metadata

    @pytest.mark.asyncio
    async def test_empty_document(self):
        """Test empty document."""
        config = ChunkingConfigV2(strategy="parent_child")
        chunker = ParentChildChunker(config)

        document = ParsedDocument(content="", metadata={})

        chunks = await chunker.chunk_async(document)

        # Should return empty list
        assert isinstance(chunks, list)
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_custom_sizes(self):
        """Test with custom parent and child sizes."""
        config = ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=2000,
            child_chunk_size=400,
            parent_child_overlap=100,
        )

        chunker = ParentChildChunker(config)

        # Medium document
        text = "This is a test. " * 300
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        assert len(chunks) > 0

        # Verify children are smaller than parents
        for chunk in chunks:
            parent_len = len(chunk.metadata["parent_content"].split())
            child_len = len(chunk.content.split())
            assert parent_len > child_len

    @pytest.mark.asyncio
    async def test_kwargs_override(self):
        """Test that kwargs can override config values."""
        config = ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=1000,
            child_chunk_size=300,
        )

        # Override with kwargs
        chunker = ParentChildChunker(config, parent_chunk_size=500, child_chunk_size=150)

        text = "Test. " * 100
        document = ParsedDocument(content=text, metadata={})

        chunks = chunker.chunk(document)

        # Chunks should reflect the overridden sizes
        assert len(chunks) > 0
