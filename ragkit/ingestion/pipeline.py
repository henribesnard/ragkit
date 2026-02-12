"""Ingestion pipeline orchestration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Protocol

import structlog
from pydantic import BaseModel

from ragkit.config.schema import IngestionConfig
from ragkit.config.schema_v2 import TextPreprocessingConfig
from ragkit.exceptions import IngestionError
from ragkit.ingestion.chunkers import create_chunker
from ragkit.ingestion.deduplication import DocumentDeduplicator
from ragkit.ingestion.metadata_extractor import MetadataExtractor
from ragkit.ingestion.parsers import create_parser
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.ingestion.preprocessing import TextPreprocessor
from ragkit.ingestion.sources import create_source_loader
from ragkit.ingestion.sources.base import RawDocument
from ragkit.models import Chunk
from ragkit.utils.async_utils import retry_async


class EmbedderProtocol(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - interface
        ...


class VectorStoreProtocol(Protocol):
    async def add(self, chunks: list[Chunk]) -> None:  # pragma: no cover - interface
        ...


class IngestionStats(BaseModel):
    documents_loaded: int = 0
    documents_parsed: int = 0
    documents_deduplicated: int = 0
    chunks_created: int = 0
    chunks_embedded: int = 0
    chunks_stored: int = 0
    documents_skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


class IngestionPipeline:
    """Orchestrate ingestion: load -> parse -> dedup -> preprocess ->
    metadata -> chunk -> embed -> store."""

    def __init__(
        self,
        config: IngestionConfig,
        embedder: EmbedderProtocol | None = None,
        vector_store: VectorStoreProtocol | None = None,
        logger: structlog.BoundLogger | None = None,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        metrics_collector: Any | None = None,
        *,
        preprocessing_config: TextPreprocessingConfig | None = None,
        deduplication_strategy: str = "none",
        deduplication_threshold: float = 0.95,
        metadata_defaults: dict | None = None,
    ) -> None:
        self.config = config
        self.embedder = embedder
        self.vector_store = vector_store
        self.logger = logger or structlog.get_logger()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.metrics = metrics_collector

        self.parser = create_parser(config.parsing)
        self.chunker = create_chunker(config.chunking, embedder=embedder)

        # ── New v2 components ─────────────────────────────────────────
        self._preprocessor: TextPreprocessor | None = None
        if preprocessing_config is not None:
            self._preprocessor = TextPreprocessor(preprocessing_config)

        self._deduplicator: DocumentDeduplicator | None = None
        if deduplication_strategy != "none":
            self._deduplicator = DocumentDeduplicator(
                strategy=deduplication_strategy,
                threshold=deduplication_threshold,
            )

        self._metadata_extractor = MetadataExtractor()
        self._metadata_defaults = metadata_defaults or {}

        if self.vector_store is not None and self.embedder is None:
            raise IngestionError("Embedder is required when a vector store is configured.")

    async def run(
        self,
        incremental: bool = False,
        state_path: Path | None = None,
    ) -> IngestionStats:
        stats = IngestionStats()
        start = time.perf_counter()
        state_file = state_path or Path(".ragkit") / "ingestion_state.json"
        state = self._load_state(state_file) if incremental else {}

        try:
            for source_config in self.config.sources:
                loader = create_source_loader(source_config)
                async for raw_doc in loader.load():
                    stats.documents_loaded += 1
                    if incremental and not self._should_process(raw_doc, state):
                        stats.documents_skipped += 1
                        continue

                    try:

                        async def _parse(raw: RawDocument = raw_doc) -> ParsedDocument:
                            return await self.parser.parse(raw)

                        parsed = await retry_async(
                            _parse,
                            max_retries=self.max_retries,
                            delay=self.retry_delay,
                        )
                        stats.documents_parsed += 1

                        # ── Deduplication ──────────────────────────────
                        if self._deduplicator is not None:
                            if self._deduplicator.is_duplicate(parsed.content):
                                stats.documents_deduplicated += 1
                                self.logger.info(
                                    "document_deduplicated",
                                    source=raw_doc.source_path,
                                )
                                continue
                            self._deduplicator.register(parsed.content)

                        # ── Text preprocessing ────────────────────────
                        if self._preprocessor is not None:
                            parsed.content = self._preprocessor.process(parsed.content)

                        # ── Metadata extraction ───────────────────────
                        doc_metadata = self._metadata_extractor.extract(
                            raw_doc,
                            parsed,
                            defaults=self._metadata_defaults,
                        )
                        # Merge structured metadata into parsed.metadata
                        flat_meta = doc_metadata.to_flat_dict()
                        parsed.metadata.update(flat_meta)

                        chunks = await self.chunker.chunk_async(parsed)
                        stats.chunks_created += len(chunks)

                        # Propagate document metadata to chunks
                        for chunk in chunks:
                            chunk.metadata.setdefault("document_id", doc_metadata.document_id)
                            chunk.metadata.setdefault("source", doc_metadata.source)
                            chunk.metadata.setdefault("source_type", doc_metadata.source_type)
                            if doc_metadata.language:
                                chunk.metadata.setdefault("language", doc_metadata.language)
                            if doc_metadata.title:
                                chunk.metadata.setdefault("title", doc_metadata.title)

                        if self.embedder:
                            embedder = self.embedder
                            assert embedder is not None

                            async def _embed(
                                current_chunks: list[Chunk] = chunks,
                                current_embedder: EmbedderProtocol = embedder,
                            ) -> list[list[float]]:
                                return await current_embedder.embed(
                                    [c.content for c in current_chunks]
                                )

                            embeddings = await retry_async(
                                _embed,
                                max_retries=self.max_retries,
                                delay=self.retry_delay,
                            )
                            if len(embeddings) != len(chunks):
                                raise IngestionError(
                                    "Embedding count mismatch: "
                                    f"{len(embeddings)} embeddings for {len(chunks)} chunks"
                                )
                            for chunk, embedding in zip(chunks, embeddings, strict=True):
                                chunk.embedding = embedding
                            stats.chunks_embedded += len(embeddings)

                        if self.vector_store:
                            vector_store = self.vector_store
                            assert vector_store is not None

                            async def _add(
                                current_chunks: list[Chunk] = chunks,
                                current_store: VectorStoreProtocol = vector_store,
                            ) -> None:
                                await current_store.add(current_chunks)

                            await retry_async(
                                _add,
                                max_retries=self.max_retries,
                                delay=self.retry_delay,
                            )
                            stats.chunks_stored += len(chunks)

                        if incremental:
                            self._update_state(raw_doc, state)
                    except Exception as exc:  # noqa: BLE001
                        stats.errors += 1
                        self.logger.error(
                            "ingestion_failed", error=str(exc), source=raw_doc.source_path
                        )
        finally:
            stats.duration_seconds = time.perf_counter() - start
            if incremental:
                self._save_state(state_file, state)
            if self.metrics is not None:
                try:
                    self.metrics.record_ingestion(stats)
                except Exception:  # noqa: BLE001
                    pass

        return stats

    def _should_process(self, raw_doc: RawDocument, state: dict[str, float]) -> bool:
        mtime = raw_doc.metadata.get("modified_time")
        if mtime is None:
            return True
        previous = state.get(raw_doc.source_path)
        return previous is None or mtime > previous

    def _update_state(self, raw_doc: RawDocument, state: dict[str, float]) -> None:
        mtime = raw_doc.metadata.get("modified_time")
        if mtime is not None:
            state[raw_doc.source_path] = float(mtime)

    def _load_state(self, path: Path) -> dict[str, float]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): float(value) for key, value in data.items()}

    def _save_state(self, path: Path, state: dict[str, float]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
