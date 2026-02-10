"""Integration tests for the chunking pipeline."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.factory import ChunkerFactory, create_chunker
from ragkit.ingestion.parsers.base import ParsedDocument


class TestChunkerFactory:
    """Tests for the ChunkerFactory."""

    def test_factory_creates_fixed_chunker(self):
        """Test factory creates fixed size chunker."""
        config = ChunkingConfigV2(strategy="fixed_size", chunk_size=512)
        chunker = ChunkerFactory.create(config)

        assert chunker is not None
        # Verify it's the right type by checking method exists
        assert hasattr(chunker, "chunk")
        assert hasattr(chunker, "chunk_async")

    def test_factory_creates_semantic_chunker(self):
        """Test factory creates semantic chunker."""
        config = ChunkingConfigV2(strategy="semantic")
        chunker = ChunkerFactory.create(config)

        assert chunker is not None

    def test_factory_creates_parent_child_chunker(self):
        """Test factory creates parent-child chunker."""
        config = ChunkingConfigV2(strategy="parent_child")
        chunker = ChunkerFactory.create(config)

        assert chunker is not None

    def test_factory_creates_sliding_window_chunker(self):
        """Test factory creates sliding window chunker."""
        config = ChunkingConfigV2(strategy="sliding_window")
        chunker = ChunkerFactory.create(config)

        assert chunker is not None

    def test_factory_creates_recursive_chunker(self):
        """Test factory creates recursive chunker."""
        config = ChunkingConfigV2(strategy="recursive")
        chunker = ChunkerFactory.create(config)

        assert chunker is not None

    def test_factory_unknown_strategy_raises(self):
        """Test factory raises on unknown strategy."""
        config = ChunkingConfigV2.model_construct(strategy="unknown_strategy")

        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            ChunkerFactory.create(config)


class TestChunkingPipeline:
    """End-to-end tests for different chunking strategies."""

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
            metadata={"title": "Python Guide", "author": "Test"}
        )

    @pytest.mark.asyncio
    async def test_fixed_size_chunking_pipeline(self, sample_document):
        """Test complete pipeline with fixed size chunking."""
        config = ChunkingConfigV2(
            strategy="fixed_size",
            chunk_size=100,
            chunk_overlap=20
        )

        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(sample_document)

        assert len(chunks) > 0

        # Verify basic properties
        for chunk in chunks:
            assert chunk.content
            assert chunk.id
            assert chunk.document_id
            assert "chunk_index" in chunk.metadata

    @pytest.mark.asyncio
    async def test_parent_child_chunking_pipeline(self, sample_document):
        """Test complete pipeline with parent-child chunking."""
        config = ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=200,
            child_chunk_size=50,
            parent_child_overlap=10
        )

        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(sample_document)

        assert len(chunks) > 0

        # Verify parent-child structure
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"
            assert "parent_id" in chunk.metadata
            assert "parent_content" in chunk.metadata
            assert "child_index_in_parent" in chunk.metadata

    @pytest.mark.asyncio
    async def test_sliding_window_chunking_pipeline(self, sample_document):
        """Test complete pipeline with sliding window chunking."""
        config = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=2,
            window_stride=1
        )

        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(sample_document)

        assert len(chunks) > 0

        # Verify window metadata
        for chunk in chunks:
            assert "window_center" in chunk.metadata
            assert "window_start" in chunk.metadata
            assert "window_end" in chunk.metadata

    @pytest.mark.asyncio
    async def test_recursive_chunking_pipeline(self, sample_document):
        """Test complete pipeline with recursive chunking."""
        config = ChunkingConfigV2(
            strategy="recursive",
            chunk_size=100,
            chunk_overlap=20,
            separators=["\n\n", "\n", ". "]
        )

        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(sample_document)

        assert len(chunks) > 0

        # Verify chunks
        for chunk in chunks:
            assert chunk.content.strip()


class TestConvenienceFunction:
    """Tests for the convenience create_chunker function."""

    def test_create_chunker_simple(self):
        """Test create_chunker with minimal args."""
        chunker = create_chunker("fixed_size", chunk_size=512)

        assert chunker is not None

    def test_create_chunker_parent_child(self):
        """Test create_chunker for parent-child."""
        chunker = create_chunker(
            "parent_child",
            parent_chunk_size=2000,
            child_chunk_size=400
        )

        assert chunker is not None

    @pytest.mark.asyncio
    async def test_create_chunker_end_to_end(self):
        """Test create_chunker end-to-end."""
        chunker = create_chunker("fixed_size", chunk_size=100, chunk_overlap=20)

        document = ParsedDocument(
            content="This is a test. " * 50,
            metadata={}
        )

        chunks = await chunker.chunk_async(document)

        assert len(chunks) > 0


class TestStrategyComparison:
    """Compare different chunking strategies on the same document."""

    @pytest.fixture
    def long_document(self):
        """A longer document for comparison."""
        content = []
        for i in range(10):
            content.append(f"Section {i}. ")
            content.append("This is a paragraph about section {i}. " * 20)
            content.append("\n\n")

        return ParsedDocument(
            content="".join(content),
            metadata={"title": "Long Doc"}
        )

    @pytest.mark.asyncio
    async def test_strategy_comparison(self, long_document):
        """Compare chunk counts across strategies."""
        strategies = {
            "fixed_size": ChunkingConfigV2(
                strategy="fixed_size",
                chunk_size=200,
                chunk_overlap=50
            ),
            "parent_child": ChunkingConfigV2(
                strategy="parent_child",
                parent_chunk_size=500,
                child_chunk_size=200,
            ),
            "sliding_window": ChunkingConfigV2(
                strategy="sliding_window",
                sentence_window_size=3,
                window_stride=1
            ),
            "recursive": ChunkingConfigV2(
                strategy="recursive",
                chunk_size=200,
                chunk_overlap=50,
                separators=["\n\n", ". "]
            ),
        }

        results = {}

        for name, config in strategies.items():
            chunker = ChunkerFactory.create(config)
            chunks = await chunker.chunk_async(long_document)
            results[name] = {
                "count": len(chunks),
                "avg_length": sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0,
            }

        # All strategies should produce chunks
        for name, stats in results.items():
            assert stats["count"] > 0, f"{name} produced no chunks"

        # Parent-child should have more chunks (children)
        # Sliding window typically creates many overlapping chunks
        # These are just sanity checks
        assert results["sliding_window"]["count"] > 0
        assert results["parent_child"]["count"] > 0


class TestMetadataPreservation:
    """Test that metadata is properly preserved through chunking."""

    @pytest.mark.asyncio
    async def test_document_metadata_in_chunks(self):
        """Test document metadata appears in chunks."""
        document = ParsedDocument(
            content="Test content. " * 100,
            metadata={
                "title": "Test Document",
                "author": "John Doe",
                "date": "2024-01-01",
                "source": "test.pdf"
            }
        )

        config = ChunkingConfigV2(
            strategy="fixed_size",
            chunk_size=100,
            add_document_title=True
        )

        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(document)

        assert len(chunks) > 0

        # Check first chunk has metadata
        first_chunk = chunks[0]
        # Original document metadata should be preserved
        assert "title" in first_chunk.metadata or "document_title" in first_chunk.metadata
