"""Factory for creating chunkers based on configured strategy."""

from __future__ import annotations

from typing import Any

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.fixed import FixedChunker
from ragkit.ingestion.chunkers.parent_child import ParentChildChunker
from ragkit.ingestion.chunkers.recursive import RecursiveChunker
from ragkit.ingestion.chunkers.semantic import SemanticChunker
from ragkit.ingestion.chunkers.sliding_window import SlidingWindowChunker


class ChunkerFactory:
    """Factory for creating chunkers based on strategy.

    Usage:
        config = ChunkingConfigV2(strategy="parent_child")
        chunker = ChunkerFactory.create(config)
        chunks = await chunker.chunk_async(document)
    """

    @staticmethod
    def create(config: ChunkingConfigV2, embedder: object | None = None) -> BaseChunker:
        """Create a chunker based on the configured strategy.

        Args:
            config: Chunking configuration
            embedder: Optional embedder for semantic chunking

        Returns:
            Chunker instance corresponding to the strategy

        Raises:
            ValueError: If the strategy is unknown or not yet implemented
        """
        strategy = config.strategy

        if strategy == "fixed_size":
            return FixedChunker(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)

        elif strategy == "semantic":
            # Import SemanticChunkingConfig for compatibility
            from ragkit.config.schema import SemanticChunkingConfig

            semantic_config = SemanticChunkingConfig(
                similarity_threshold=config.semantic_similarity_threshold,
                min_chunk_size=config.min_chunk_size,
                max_chunk_size=config.max_chunk_size,
            )
            return SemanticChunker(config=semantic_config, embedder=embedder)

        elif strategy == "parent_child":
            return ParentChildChunker(config=config)

        elif strategy == "sliding_window":
            return SlidingWindowChunker(config=config)

        elif strategy == "recursive":
            return RecursiveChunker(config=config)

        elif strategy == "sentence_based":
            # TODO: Implement SentenceChunker
            # For now, use sliding window with stride=1 as approximation
            from ragkit.config.schema_v2 import ChunkingConfigV2

            sentence_config = ChunkingConfigV2.model_validate(
                {
                    "strategy": "sliding_window",
                    "sentence_window_size": 1,
                    "window_stride": 1,
                }
            )
            return SlidingWindowChunker(config=sentence_config)

        elif strategy == "paragraph_based":
            # TODO: Implement ParagraphChunker
            # For now, use recursive with "\n\n" separator
            from ragkit.config.schema_v2 import ChunkingConfigV2

            paragraph_config = ChunkingConfigV2.model_validate(
                {
                    "strategy": "recursive",
                    "separators": ["\n\n", "\n"],
                    "chunk_size": config.chunk_size,
                    "chunk_overlap": config.chunk_overlap,
                }
            )
            return RecursiveChunker(config=paragraph_config)

        elif strategy == "markdown_header":
            # TODO: Implement MarkdownHeaderChunker
            # For now, use recursive with markdown headers
            raise NotImplementedError(
                "MarkdownHeaderChunker not yet implemented. "
                "Use 'recursive' strategy with markdown separators as a workaround."
            )

        else:
            raise ValueError(
                f"Unknown chunking strategy: {strategy}. "
                f"Supported strategies: fixed_size, semantic, parent_child, "
                f"sliding_window, recursive, sentence_based, paragraph_based"
            )


def create_chunker(
    strategy: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    **kwargs: Any,
) -> BaseChunker:
    """Convenience function to create a chunker with minimal configuration.

    Args:
        strategy: Chunking strategy name
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        **kwargs: Additional strategy-specific parameters

    Returns:
        Configured chunker instance

    Example:
        # Simple fixed-size chunker
        chunker = create_chunker("fixed_size", chunk_size=512)

        # Parent-child chunker
        chunker = create_chunker(
            "parent_child",
            parent_chunk_size=2000,
            child_chunk_size=400
        )

        # Semantic chunker with custom threshold
        chunker = create_chunker(
            "semantic",
            semantic_similarity_threshold=0.85,
            embedder=my_embedder
        )
    """
    data: dict[str, Any] = {
        "strategy": strategy,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        **kwargs,
    }
    config = ChunkingConfigV2.model_validate(data)

    embedder = kwargs.get("embedder")
    return ChunkerFactory.create(config, embedder=embedder)
