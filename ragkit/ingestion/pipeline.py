"""Ingestion pipeline orchestration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Protocol

import structlog
from pydantic import BaseModel

from ragkit.config.schema import IngestionConfig
from ragkit.exceptions import IngestionError
from ragkit.ingestion.chunkers import create_chunker
from ragkit.ingestion.parsers import create_parser
from ragkit.ingestion.parsers.base import ParsedDocument
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
    chunks_created: int = 0
    chunks_embedded: int = 0
    chunks_stored: int = 0
    documents_skipped: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


class IngestionPipeline:
    """Orchestrate ingestion: load -> parse -> chunk -> embed -> store."""

    def __init__(
        self,
        config: IngestionConfig,
        embedder: EmbedderProtocol | None = None,
        vector_store: VectorStoreProtocol | None = None,
        logger: structlog.BoundLogger | None = None,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        metrics_collector: Any | None = None,
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

                        chunks = await self.chunker.chunk_async(parsed)
                        stats.chunks_created += len(chunks)

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
                            for chunk, embedding in zip(chunks, embeddings):
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
