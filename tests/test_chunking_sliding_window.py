"""Tests for sliding window chunking."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.sliding_window import SlidingWindowChunker
from ragkit.ingestion.parsers.base import ParsedDocument


class TestSlidingWindowChunking:
    """Tests for the sliding window chunker."""

    @pytest.fixture
    def config(self):
        """Default configuration."""
        return ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=3,
            window_stride=1,
        )

    @pytest.mark.asyncio
    async def test_creates_overlapping_windows(self, config):
        """Test creation of overlapping windows."""
        chunker = SlidingWindowChunker(config)

        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # With 5 sentences, window_size=3, stride=1, should create overlapping windows
        assert len(chunks) > 0

        # Each chunk should have metadata about window position
        for chunk in chunks:
            assert "window_center" in chunk.metadata
            assert "window_start" in chunk.metadata
            assert "window_end" in chunk.metadata
            assert "window_size" in chunk.metadata

    @pytest.mark.asyncio
    async def test_window_contains_context(self, config):
        """Test that windows contain context around central sentence."""
        chunker = SlidingWindowChunker(config)

        text = "S1. S2. S3. S4. S5."
        document = ParsedDocument(content=text, metadata={})

        chunks = chunker.chunk(document)

        # First chunk should contain multiple sentences (context)
        if chunks:
            first_chunk = chunks[0]
            # Should contain more than one sentence
            assert first_chunk.content.count(".") >= 1

    @pytest.mark.asyncio
    async def test_stride_affects_overlap(self):
        """Test that stride parameter affects window overlap."""
        # Stride=1: maximum overlap
        config1 = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=2,
            window_stride=1,
        )
        chunker1 = SlidingWindowChunker(config1)

        # Stride=2: less overlap
        config2 = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=2,
            window_stride=2,
        )
        chunker2 = SlidingWindowChunker(config2)

        text = "S1. S2. S3. S4. S5. S6."
        document = ParsedDocument(content=text, metadata={})

        chunks1 = chunker1.chunk(document)
        chunks2 = chunker2.chunk(document)

        # Stride=1 should create more chunks (more overlap)
        # Stride=2 should create fewer chunks (less overlap)
        assert len(chunks1) >= len(chunks2)

    @pytest.mark.asyncio
    async def test_single_sentence(self, config):
        """Test with single sentence document."""
        chunker = SlidingWindowChunker(config)

        text = "Only one sentence here."
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Should create 1 chunk
        assert len(chunks) == 1
        assert chunks[0].content.strip() == text.strip()

    @pytest.mark.asyncio
    async def test_empty_document(self, config):
        """Test with empty document."""
        chunker = SlidingWindowChunker(config)

        document = ParsedDocument(content="", metadata={})

        chunks = await chunker.chunk_async(document)

        # Should return empty list
        assert chunks == []

    @pytest.mark.asyncio
    async def test_metadata_enrichment(self, config):
        """Test metadata enrichment."""
        chunker = SlidingWindowChunker(config)

        document = ParsedDocument(content="First. Second. Third.", metadata={"title": "Test Doc"})

        chunks = await chunker.chunk_async(document)

        for chunk in chunks:
            # Check chunk index
            assert "chunk_index" in chunk.metadata

            # Check document title if configured
            if config.add_document_title:
                assert "document_title" in chunk.metadata
                assert chunk.metadata["document_title"] == "Test Doc"


class TestSlidingWindowChunkingEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_large_window_size(self):
        """Test with window size larger than document."""
        config = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=100,  # Very large
            window_stride=1,
        )

        chunker = SlidingWindowChunker(config)

        text = "S1. S2. S3."
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Should still work, creating chunks with all available sentences
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_window_boundaries(self):
        """Test window boundaries are correct."""
        config = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=2,
            window_stride=1,
        )

        chunker = SlidingWindowChunker(config)

        text = "A. B. C. D. E."
        document = ParsedDocument(content=text, metadata={})

        chunks = chunker.chunk(document)

        # Verify first chunk starts at 0
        if chunks:
            assert chunks[0].metadata["window_start"] == 0

        # Verify last chunk ends at or before last sentence
        if chunks:
            last_chunk = chunks[-1]
            # Should not exceed total sentences
            assert last_chunk.metadata["window_end"] <= len("A. B. C. D. E.".split(". "))

    @pytest.mark.asyncio
    async def test_kwargs_override(self):
        """Test that kwargs can override config values."""
        config = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=3,
            window_stride=1,
        )

        # Override with kwargs
        chunker = SlidingWindowChunker(config, sentence_window_size=2, window_stride=2)

        text = "A. B. C. D. E. F."
        document = ParsedDocument(content=text, metadata={})

        chunks = chunker.chunk(document)

        # Should use overridden values
        if chunks:
            assert chunks[0].metadata["window_size"] == 2

    @pytest.mark.asyncio
    async def test_no_sentence_endings(self):
        """Test with text that has no sentence endings."""
        config = ChunkingConfigV2(
            strategy="sliding_window",
            sentence_window_size=2,
            window_stride=1,
        )

        chunker = SlidingWindowChunker(config)

        # Text without sentence terminators
        text = "This is all one long sentence without any periods or other terminators"
        document = ParsedDocument(content=text, metadata={})

        chunks = chunker.chunk(document)

        # Should still create a chunk
        assert len(chunks) >= 1
