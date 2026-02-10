"""Sliding window chunking for Q&A and FAQ.

Sliding window chunking creates chunks with local context:
- Each central sentence is surrounded by N sentences before/after
- Useful for Q&A where a sentence alone doesn't make sense
- Intentional redundancy to maximize recall

Example with window_size=3, stride=1:
    Sentences: [S1, S2, S3, S4, S5, S6]

    Window 1: [S1, S2, S3] (central = S2)
    Window 2: [S2, S3, S4] (central = S3)
    Window 3: [S3, S4, S5] (central = S4)
    ...
"""

from __future__ import annotations

import re
from pathlib import Path

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.models import Chunk

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    return sentences or [text] if text.strip() else []


def _document_id(document: ParsedDocument) -> str:
    """Extract document ID from metadata."""
    raw_id = document.metadata.get("document_id") or document.metadata.get("source_path")
    if raw_id:
        return Path(str(raw_id)).stem
    return "document"


class SlidingWindowChunker(BaseChunker):
    """Chunker with sliding window for Q&A.

    Each chunk contains a central sentence + N context sentences before/after.

    Example:
        window_size=3, stride=1
        Sentences: ["S1", "S2", "S3", "S4", "S5"]

        Chunk 0: ["S1", "S2", "S3"] (center=0)
        Chunk 1: ["S1", "S2", "S3", "S4"] (center=1)
        Chunk 2: ["S2", "S3", "S4", "S5"] (center=2)
        Chunk 3: ["S3", "S4", "S5"] (center=3)
        Chunk 4: ["S4", "S5"] (center=4)
    """

    def __init__(self, config: ChunkingConfigV2 | None = None, **kwargs):
        """Initialize the chunker.

        Args:
            config: Configuration with sentence_window_size and window_stride
            **kwargs: Optional override for window_size, stride
        """
        self.config = config or ChunkingConfigV2()

        # Allow kwargs override
        self.window_size = kwargs.get("sentence_window_size", self.config.sentence_window_size)
        self.stride = kwargs.get("window_stride", self.config.window_stride)

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Create chunks with sliding window.

        Args:
            document: Parsed document to chunk

        Returns:
            List of chunks with local context
        """
        # Split into sentences
        sentences = _split_sentences(document.content)

        if not sentences:
            return []

        chunks = []
        doc_id = _document_id(document)

        # Sliding window
        for i in range(0, len(sentences), self.stride):
            # Calculate window bounds
            # Window centered on sentence i
            center_idx = i
            start_idx = max(0, center_idx - self.window_size)
            end_idx = min(len(sentences), center_idx + self.window_size + 1)

            # Extract window sentences
            window_sentences = sentences[start_idx:end_idx]
            chunk_content = " ".join(window_sentences)

            # Create chunk
            metadata = dict(document.metadata)
            metadata.update(
                {
                    "chunk_index": len(chunks),
                    "window_center": center_idx,
                    "window_start": start_idx,
                    "window_end": end_idx,
                    "window_size": self.window_size,
                    "num_sentences": len(window_sentences),
                }
            )

            # Enrich metadata
            if self.config.add_document_title and "title" in document.metadata:
                metadata["document_title"] = document.metadata["title"]

            chunk = Chunk(
                id=f"{doc_id}-chunk-{len(chunks)}",
                document_id=doc_id,
                content=chunk_content,
                metadata=metadata,
            )

            chunks.append(chunk)

            # Stop if we reached the end
            if end_idx >= len(sentences):
                break

        return chunks

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        """Create chunks with sliding window (async).

        Args:
            document: Parsed document to chunk

        Returns:
            List of chunks with local context
        """
        return self.chunk(document)
