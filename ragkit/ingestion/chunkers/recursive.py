"""Recursive chunking for structured content (Markdown, code).

Recursive chunking respects document structure by splitting on hierarchical separators:
1. Try splitting on "\n\n" (paragraphs)
2. If chunks still too large, split on "\n" (lines)
3. If still too large, split on ". " (sentences)
4. If still too large, split on " " (words)
5. If still too large, split on "" (characters)

This preserves natural boundaries in the document while respecting size constraints.
"""

from __future__ import annotations

import re
from pathlib import Path

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.fixed import _detokenize, _tokenize
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.models import Chunk


def _document_id(document: ParsedDocument) -> str:
    """Extract document ID from metadata."""
    raw_id = document.metadata.get("document_id") or document.metadata.get("source_path")
    if raw_id:
        return Path(str(raw_id)).stem
    return "document"


class RecursiveChunker(BaseChunker):
    """Recursive chunker that respects document structure.

    Tries to split on hierarchical separators in order:
    1. Double newlines (paragraphs)
    2. Single newlines (lines)
    3. Periods with space (sentences)
    4. Spaces (words)
    5. Characters (last resort)

    This preserves natural boundaries while respecting chunk size constraints.

    Example:
        For a Markdown document:
        ```markdown
        # Header 1

        This is a paragraph.
        It has multiple sentences.

        ## Header 2

        Another paragraph here.
        ```

        Will first split on "\\n\\n" (paragraphs), creating coherent chunks.
    """

    def __init__(self, config: ChunkingConfigV2 | None = None, **kwargs):
        """Initialize the chunker.

        Args:
            config: Configuration with chunk_size, chunk_overlap, separators
            **kwargs: Optional override for chunk_size, chunk_overlap, separators
        """
        self.config = config or ChunkingConfigV2()

        # Allow kwargs override
        self.chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        self.chunk_overlap = kwargs.get("chunk_overlap", self.config.chunk_overlap)
        self.keep_separator = kwargs.get("keep_separator", self.config.keep_separator)
        self.separators = kwargs.get("separators", self.config.separators)

        # Use custom regex if provided
        if self.config.separator_regex:
            self.separator_regex = re.compile(self.config.separator_regex)
        else:
            self.separator_regex = None

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Create chunks recursively.

        Args:
            document: Parsed document to chunk

        Returns:
            List of chunks respecting document structure
        """
        chunks_content = self._split_text(document.content, self.separators)

        # Create Chunk objects
        chunks = []
        doc_id = _document_id(document)

        for idx, content in enumerate(chunks_content):
            if not content.strip():
                continue

            metadata = dict(document.metadata)
            metadata["chunk_index"] = idx

            if self.config.add_document_title and "title" in document.metadata:
                metadata["document_title"] = document.metadata["title"]

            chunk = Chunk(
                id=f"{doc_id}-chunk-{idx}",
                document_id=doc_id,
                content=content,
                metadata=metadata,
            )

            chunks.append(chunk)

        return chunks

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        """Create chunks recursively (async).

        Args:
            document: Parsed document to chunk

        Returns:
            List of chunks respecting document structure
        """
        return self.chunk(document)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using hierarchical separators.

        Args:
            text: Text to split
            separators: List of separators in order of priority

        Returns:
            List of text chunks
        """
        # Base case: no more separators or text is short enough
        tokens, _ = _tokenize(text)
        if len(tokens) <= self.chunk_size or not separators:
            return [text] if text.strip() else []

        # Try splitting with first separator
        separator = separators[0]
        remaining_separators = separators[1:]

        # Split text
        if separator == "":
            # Character-level split
            splits = list(text)
        else:
            splits = text.split(separator)

        # Rejoin splits with overlap
        result = []
        current_chunk = []
        current_length = 0

        for i, split in enumerate(splits):
            if not split.strip() and separator != "":
                continue

            # Add separator back if configured
            if self.keep_separator and separator and i > 0:
                split = separator + split

            tokens, _ = _tokenize(split)
            split_length = len(tokens)

            # If this split alone exceeds chunk_size, recursively split it
            if split_length > self.chunk_size and remaining_separators:
                # First, flush current chunk
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    result.append(chunk_text)
                    current_chunk = []
                    current_length = 0

                # Recursively split this large piece
                sub_chunks = self._split_text(split, remaining_separators)
                result.extend(sub_chunks)
                continue

            # Check if adding this split exceeds chunk_size
            if current_length + split_length > self.chunk_size and current_chunk:
                # Flush current chunk
                chunk_text = "".join(current_chunk)
                result.append(chunk_text)

                # Start new chunk with overlap
                overlap_tokens = min(self.chunk_overlap, current_length)
                if overlap_tokens > 0:
                    # Get last N tokens from current chunk for overlap
                    overlap_text = "".join(current_chunk)
                    overlap_tok, overlap_enc = _tokenize(overlap_text)
                    if len(overlap_tok) > overlap_tokens:
                        overlap_tok = overlap_tok[-overlap_tokens:]
                        overlap_text = _detokenize(overlap_tok, overlap_enc)
                        current_chunk = [overlap_text]
                        current_length = len(overlap_tok)
                    else:
                        current_chunk = []
                        current_length = 0
                else:
                    current_chunk = []
                    current_length = 0

            # Add split to current chunk
            current_chunk.append(split)
            current_length += split_length

        # Don't forget last chunk
        if current_chunk:
            result.append("".join(current_chunk) if separator == "" else "".join(current_chunk))

        return result
