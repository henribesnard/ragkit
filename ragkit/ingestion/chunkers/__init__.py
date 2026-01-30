"""Chunker factory and exports."""

from __future__ import annotations

from ragkit.config.schema import ChunkingConfig, SemanticChunkingConfig
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.fixed import FixedChunker
from ragkit.ingestion.chunkers.semantic import SemanticChunker


def create_chunker(config: ChunkingConfig, embedder: object | None = None) -> BaseChunker:
    if config.strategy == "fixed":
        return FixedChunker(
            chunk_size=config.fixed.chunk_size,
            chunk_overlap=config.fixed.chunk_overlap,
        )
    if config.strategy == "semantic":
        return SemanticChunker(config.semantic, embedder=embedder)
    raise ValueError(f"Unknown chunking strategy: {config.strategy}")


__all__ = ["BaseChunker", "FixedChunker", "SemanticChunker", "create_chunker"]
