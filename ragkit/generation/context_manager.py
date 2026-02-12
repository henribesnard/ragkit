"""Context preparation for LLM prompts."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.citation_formatter import CitationFormatter
from ragkit.generation.utils.compression import compress_context

logger = logging.getLogger(__name__)


class Tokenizer(Protocol):
    """Minimal tokenizer protocol used for context sizing."""

    def encode(self, text: str) -> list[Any]: ...

    def decode(self, tokens: list[Any]) -> str: ...


class SimpleTokenizer:
    """Whitespace-preserving tokenizer fallback."""

    def encode(self, text: str) -> list[str]:
        import re

        return re.findall(r"\S+|\s+", text)

    def decode(self, tokens: list[str]) -> str:
        return "".join(tokens)


@dataclass
class NormalizedDocument:
    content: str
    metadata: dict[str, Any]


class ContextManager:
    """Prepare and format context for LLM generation."""

    def __init__(
        self,
        config: LLMGenerationConfigV2,
        tokenizer: Tokenizer | None = None,
        citation_formatter: CitationFormatter | None = None,
    ) -> None:
        self.config = config
        self.tokenizer = tokenizer or _default_tokenizer()
        self.citation_formatter = citation_formatter or CitationFormatter(config)

    def prepare_context(
        self,
        documents: Iterable[Any],
        max_tokens: int | None = None,
    ) -> str:
        """Prepare context within token budget."""
        max_tokens = max_tokens or self.config.max_context_tokens
        normalized = self._normalize_documents(documents)
        ordered = self._order_documents(normalized)
        formatted = self._format_documents(ordered)
        truncated = self._truncate_to_limit(formatted, max_tokens)

        if self.config.context_compression:
            truncated = compress_context(
                truncated,
                ratio=self.config.compression_ratio,
                tokenizer=self.tokenizer,
            )

        return truncated

    def _normalize_documents(self, documents: Iterable[Any]) -> list[NormalizedDocument]:
        normalized: list[NormalizedDocument] = []
        for doc in documents:
            content, metadata = self._extract_content_metadata(doc)
            if content:
                normalized.append(NormalizedDocument(content=content, metadata=metadata))
        return normalized

    def _extract_content_metadata(self, doc: Any) -> tuple[str, dict[str, Any]]:
        if doc is None:
            return "", {}

        if hasattr(doc, "chunk"):
            chunk = doc.chunk
            metadata = getattr(chunk, "metadata", {}) or {}
            metadata = dict(metadata)
            if hasattr(doc, "score"):
                metadata["score"] = doc.score
            return getattr(chunk, "content", ""), metadata

        if hasattr(doc, "content"):
            metadata = getattr(doc, "metadata", {}) or {}
            return getattr(doc, "content", ""), dict(metadata)

        if isinstance(doc, dict):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {}) or {}
            return str(content), dict(metadata)

        return str(doc), {}

    def _order_documents(
        self,
        documents: list[NormalizedDocument],
    ) -> list[NormalizedDocument]:
        if self.config.context_ordering == "relevance":
            return documents
        if self.config.context_ordering == "chronological":
            return sorted(
                documents,
                key=lambda d: str(d.metadata.get("date", "")),
            )
        if self.config.context_ordering == "lost_in_middle":
            return _lost_in_middle_ordering(documents)
        return documents

    def _format_documents(self, documents: list[NormalizedDocument]) -> str:
        formatted_lines = ["Context:\n"]
        for index, doc in enumerate(documents, start=1):
            header = self.citation_formatter.format_source_header(index, doc.metadata)
            formatted_lines.append(f"{header}\n{doc.content}\n")
        return "\n".join(formatted_lines).strip() + "\n"

    def _truncate_to_limit(self, context: str, max_tokens: int) -> str:
        tokens = self.tokenizer.encode(context)
        if len(tokens) <= max_tokens:
            return context

        strategy = self.config.context_window_strategy
        if strategy == "truncate_end":
            return self.tokenizer.decode(tokens[:max_tokens])
        if strategy == "truncate_middle":
            head = int(max_tokens * 0.4)
            tail = max_tokens - head
            kept = tokens[:head] + tokens[-tail:]
            return self.tokenizer.decode(kept)
        if strategy == "summarize_overflow":
            summary_marker = "\n...[summary omitted due to length]...\n"
            head = int(max_tokens * 0.5)
            tail = max_tokens - head
            kept = tokens[:head] + tokens[-tail:]
            return self.tokenizer.decode(kept) + summary_marker
        if strategy == "sliding_window":
            return self.tokenizer.decode(tokens[-max_tokens:])

        return self.tokenizer.decode(tokens[:max_tokens])


def _lost_in_middle_ordering(
    documents: list[NormalizedDocument],
) -> list[NormalizedDocument]:
    if not documents:
        return []

    ordered: list[NormalizedDocument | None] = [None] * len(documents)
    left = 0
    right = len(documents) - 1
    for idx, doc in enumerate(documents):
        if idx % 2 == 0:
            ordered[left] = doc
            left += 1
        else:
            ordered[right] = doc
            right -= 1

    return [doc for doc in ordered if doc is not None]


def _default_tokenizer() -> Tokenizer:
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")

        class TikTokenizer:
            def encode(self, text: str) -> list[int]:
                return encoding.encode(text)

            def decode(self, tokens: list[int]) -> str:
                return encoding.decode(tokens)

        return TikTokenizer()
    except Exception:  # noqa: BLE001
        logger.debug("tiktoken not available, using SimpleTokenizer")
        return SimpleTokenizer()
