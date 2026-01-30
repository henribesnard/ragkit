"""Semantic chunking implementation."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable

from ragkit.config.schema import SemanticChunkingConfig
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.fixed import _detokenize, _tokenize
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.models import Chunk

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    return sentences or [text] if text.strip() else []


def _document_id(document: ParsedDocument) -> str:
    raw_id = document.metadata.get("document_id") or document.metadata.get("source_path")
    if raw_id:
        return Path(str(raw_id)).stem
    return "document"


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _maybe_embed(embedder: object, texts: Iterable[str]) -> list[list[float]] | None:
    if embedder is None:
        return None
    embed_fn = getattr(embedder, "embed_texts", None)
    if embed_fn is None:
        return None
    return embed_fn(list(texts))


class SemanticChunker(BaseChunker):
    """Chunking based on sentence similarity thresholds."""

    def __init__(self, config: SemanticChunkingConfig, embedder: object | None = None):
        self.similarity_threshold = config.similarity_threshold
        self.min_size = config.min_chunk_size
        self.max_size = config.max_chunk_size
        self.embedder = embedder

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        sentences = _split_sentences(document.content)
        if not sentences:
            return []

        embeddings = _maybe_embed(self.embedder, sentences)

        doc_id = _document_id(document)
        chunks: list[Chunk] = []
        current: list[str] = []
        current_tokens = 0

        for idx, sentence in enumerate(sentences):
            sentence_tokens, _ = _tokenize(sentence)
            sentence_len = len(sentence_tokens)

            current.append(sentence)
            current_tokens += sentence_len

            should_split = False
            if current_tokens >= self.max_size:
                should_split = True
            elif embeddings is not None and idx < len(sentences) - 1:
                similarity = _cosine_similarity(embeddings[idx], embeddings[idx + 1])
                if similarity < self.similarity_threshold and current_tokens >= self.min_size:
                    should_split = True

            if should_split:
                content = " ".join(current).strip()
                tokens, encoding = _tokenize(content)
                metadata = dict(document.metadata)
                metadata.update({"chunk_index": len(chunks)})
                chunks.append(
                    Chunk(
                        id=f"{doc_id}-chunk-{len(chunks)}",
                        document_id=doc_id,
                        content=_detokenize(tokens, encoding),
                        metadata=metadata,
                    )
                )
                current = []
                current_tokens = 0

        if current:
            content = " ".join(current).strip()
            tokens, encoding = _tokenize(content)
            metadata = dict(document.metadata)
            metadata.update({"chunk_index": len(chunks)})
            chunks.append(
                Chunk(
                    id=f"{doc_id}-chunk-{len(chunks)}",
                    document_id=doc_id,
                    content=_detokenize(tokens, encoding),
                    metadata=metadata,
                )
            )

        return chunks
