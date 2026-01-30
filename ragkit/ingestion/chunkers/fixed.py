"""Fixed-size chunking implementation."""

from __future__ import annotations

import re
from pathlib import Path

from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.models import Chunk

_TOKEN_RE = re.compile(r"\S+")


def _tokenize(text: str) -> tuple[list[int] | list[str], object | None]:
    try:
        import tiktoken  # type: ignore
    except Exception:
        return _TOKEN_RE.findall(text), None

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode(text), encoding
    except Exception:
        return _TOKEN_RE.findall(text), None


def _detokenize(tokens: list[int] | list[str], encoding: object | None) -> str:
    if encoding is not None and tokens and isinstance(tokens[0], int):
        return encoding.decode(tokens)  # type: ignore[attr-defined]
    return " ".join(str(token) for token in tokens)


def _document_id(document: ParsedDocument) -> str:
    raw_id = document.metadata.get("document_id") or document.metadata.get("source_path")
    if raw_id:
        return Path(str(raw_id)).stem
    return "document"


class FixedChunker(BaseChunker):
    """Chunking with fixed token size and overlap."""

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        tokens, encoding = _tokenize(document.content)
        if not tokens:
            return []

        step = max(self.chunk_size - self.chunk_overlap, 1)
        chunks: list[Chunk] = []
        doc_id = _document_id(document)

        for idx, start in enumerate(range(0, len(tokens), step)):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            content = _detokenize(chunk_tokens, encoding)
            metadata = dict(document.metadata)
            metadata.update({"chunk_index": idx, "start_token": start, "end_token": end})
            chunks.append(
                Chunk(
                    id=f"{doc_id}-chunk-{idx}",
                    document_id=doc_id,
                    content=content,
                    metadata=metadata,
                )
            )
            if end >= len(tokens):
                break
        return chunks
