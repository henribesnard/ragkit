"""Chunker factory and exports."""

from __future__ import annotations

from ragkit.config.schema import ChunkingConfig
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.factory import ChunkerFactory, create_chunker as create_chunker_v2
from ragkit.ingestion.chunkers.fixed import FixedChunker
from ragkit.ingestion.chunkers.parent_child import ParentChildChunker
from ragkit.ingestion.chunkers.recursive import RecursiveChunker
from ragkit.ingestion.chunkers.semantic import SemanticChunker
from ragkit.ingestion.chunkers.sliding_window import SlidingWindowChunker


def create_chunker(config: ChunkingConfig, embedder: object | None = None) -> BaseChunker:
    """Legacy create_chunker function for backward compatibility."""
    if config.strategy == "fixed":
        return FixedChunker(
            chunk_size=config.fixed.chunk_size,
            chunk_overlap=config.fixed.chunk_overlap,
        )
    if config.strategy == "semantic":
        return SemanticChunker(config.semantic, embedder=embedder)
    raise ValueError(f"Unknown chunking strategy: {config.strategy}")


__all__ = [
    "BaseChunker",
    "FixedChunker",
    "SemanticChunker",
    "ParentChildChunker",
    "SlidingWindowChunker",
    "RecursiveChunker",
    "ChunkerFactory",
    "create_chunker",
    "create_chunker_v2",
]
