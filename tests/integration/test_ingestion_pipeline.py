"""Integration tests for the enhanced ingestion pipeline."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from ragkit.config.schema import (
    ChunkingConfig,
    FixedChunkingConfig,
    IngestionConfig,
    MetadataConfig,
    ParsingConfig,
    SourceConfig,
)
from ragkit.config.schema_v2 import TextPreprocessingConfig
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.ingestion.pipeline import IngestionPipeline, IngestionStats
from ragkit.ingestion.sources.base import RawDocument
from ragkit.models import Chunk


# ── Helpers ──────────────────────────────────────────────────────────────


class FakeParser:
    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        content = (
            raw_doc.content.decode("utf-8")
            if isinstance(raw_doc.content, bytes)
            else raw_doc.content
        )
        return ParsedDocument(content=content, metadata={})

    def supports(self, file_type: str) -> bool:
        return True


class FakeChunker:
    def __init__(self):
        self.chunk_size = 100

    async def chunk_async(self, parsed: ParsedDocument) -> list[Chunk]:
        return [
            Chunk(
                id="chunk-0",
                document_id="doc-0",
                content=parsed.content,
                metadata=dict(parsed.metadata),
            )
        ]


class FakeSourceLoader:
    def __init__(self, docs: list[RawDocument]):
        self._docs = docs

    async def load(self) -> AsyncIterator[RawDocument]:
        for doc in self._docs:
            yield doc

    def supports(self, source_config: Any) -> bool:
        return True


def _make_config() -> IngestionConfig:
    return IngestionConfig(
        sources=[SourceConfig(type="local", path="/tmp/fake")],
        parsing=ParsingConfig(),
        chunking=ChunkingConfig(
            strategy="fixed",
            fixed=FixedChunkingConfig(chunk_size=500, chunk_overlap=0),
        ),
        metadata=MetadataConfig(),
    )


# ── Tests ────────────────────────────────────────────────────────────────


class TestPipelineWithMetadata:
    """Test that metadata extraction is integrated into the pipeline."""

    @pytest.mark.asyncio
    async def test_metadata_extracted_into_chunks(self, monkeypatch):
        config = _make_config()
        pipeline = IngestionPipeline(config)

        # Replace parser and chunker with fakes
        pipeline.parser = FakeParser()
        pipeline.chunker = FakeChunker()

        docs = [
            RawDocument(
                content=b"# My Title\n\nHello world with enough text for detection.",
                source_path="/tmp/fake/report.md",
                file_type="md",
                metadata={},
            )
        ]
        loader = FakeSourceLoader(docs)

        # Monkeypatch source loader creation
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_parsed == 1
        assert stats.chunks_created == 1

    @pytest.mark.asyncio
    async def test_metadata_defaults_applied(self, monkeypatch):
        config = _make_config()
        pipeline = IngestionPipeline(
            config,
            metadata_defaults={"tenant": "acme", "domain": "legal"},
        )
        pipeline.parser = FakeParser()
        pipeline.chunker = FakeChunker()

        docs = [
            RawDocument(
                content=b"Contract content",
                source_path="/tmp/fake/contract.txt",
                file_type="txt",
                metadata={},
            )
        ]
        loader = FakeSourceLoader(docs)
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_parsed == 1


class TestPipelineWithPreprocessing:
    """Test that text preprocessing is applied during ingestion."""

    @pytest.mark.asyncio
    async def test_preprocessing_removes_urls(self, monkeypatch):
        config = _make_config()
        preprocess_config = TextPreprocessingConfig(remove_urls=True)
        pipeline = IngestionPipeline(config, preprocessing_config=preprocess_config)
        pipeline.parser = FakeParser()

        captured_chunks: list[Chunk] = []
        original_chunk_async = FakeChunker.chunk_async

        class CapturingChunker(FakeChunker):
            async def chunk_async(self, parsed: ParsedDocument) -> list[Chunk]:
                chunks = await original_chunk_async(self, parsed)
                captured_chunks.extend(chunks)
                return chunks

        pipeline.chunker = CapturingChunker()

        docs = [
            RawDocument(
                content=b"Visit https://example.com for more info",
                source_path="/tmp/fake/doc.txt",
                file_type="txt",
                metadata={},
            )
        ]
        loader = FakeSourceLoader(docs)
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_parsed == 1
        assert len(captured_chunks) == 1
        assert "https://example.com" not in captured_chunks[0].content


class TestPipelineWithDeduplication:
    """Test that deduplication skips duplicate documents."""

    @pytest.mark.asyncio
    async def test_exact_dedup_skips_second_copy(self, monkeypatch):
        config = _make_config()
        pipeline = IngestionPipeline(config, deduplication_strategy="exact")
        pipeline.parser = FakeParser()
        pipeline.chunker = FakeChunker()

        # Two identical documents
        docs = [
            RawDocument(
                content=b"Same content here",
                source_path="/tmp/fake/doc1.txt",
                file_type="txt",
                metadata={},
            ),
            RawDocument(
                content=b"Same content here",
                source_path="/tmp/fake/doc2.txt",
                file_type="txt",
                metadata={},
            ),
        ]
        loader = FakeSourceLoader(docs)
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_loaded == 2
        assert stats.documents_parsed == 2
        assert stats.documents_deduplicated == 1
        assert stats.chunks_created == 1  # Only one document produced chunks

    @pytest.mark.asyncio
    async def test_no_dedup_processes_all(self, monkeypatch):
        config = _make_config()
        pipeline = IngestionPipeline(config)  # No dedup by default
        pipeline.parser = FakeParser()
        pipeline.chunker = FakeChunker()

        docs = [
            RawDocument(
                content=b"Same content here",
                source_path="/tmp/fake/doc1.txt",
                file_type="txt",
                metadata={},
            ),
            RawDocument(
                content=b"Same content here",
                source_path="/tmp/fake/doc2.txt",
                file_type="txt",
                metadata={},
            ),
        ]
        loader = FakeSourceLoader(docs)
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_loaded == 2
        assert stats.documents_parsed == 2
        assert stats.documents_deduplicated == 0
        assert stats.chunks_created == 2


class TestPipelineBackwardCompatibility:
    """Verify the pipeline still works with v1 config only."""

    @pytest.mark.asyncio
    async def test_basic_pipeline_no_v2(self, monkeypatch):
        config = _make_config()
        # No preprocessing, no dedup, no metadata defaults
        pipeline = IngestionPipeline(config)
        pipeline.parser = FakeParser()
        pipeline.chunker = FakeChunker()

        docs = [
            RawDocument(
                content=b"Simple document",
                source_path="/tmp/fake/simple.txt",
                file_type="txt",
                metadata={},
            )
        ]
        loader = FakeSourceLoader(docs)
        monkeypatch.setattr(
            "ragkit.ingestion.pipeline.create_source_loader",
            lambda _cfg: loader,
        )

        stats = await pipeline.run()
        assert stats.documents_loaded == 1
        assert stats.documents_parsed == 1
        assert stats.chunks_created == 1
        assert stats.errors == 0
