"""Retrieval engine orchestration."""

from __future__ import annotations

import re
from typing import Iterable

import structlog

from ragkit.config.schema import RetrievalConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.models import Chunk, RetrievalResult
from ragkit.retrieval.fusion import ScoreFusion
from ragkit.retrieval.lexical import LexicalRetriever
from ragkit.retrieval.rerank import BaseReranker, create_reranker
from ragkit.retrieval.semantic import SemanticRetriever
from ragkit.vectorstore.base import BaseVectorStore


class RetrievalEngine:
    """Orchestrate semantic + lexical retrieval with fusion and reranking."""

    def __init__(
        self,
        config: RetrievalConfig,
        vector_store: BaseVectorStore,
        embedder: BaseEmbedder,
        lexical_chunks: list[Chunk] | None = None,
        logger: structlog.BoundLogger | None = None,
    ) -> None:
        self.config = config
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = logger or structlog.get_logger()

        self.semantic = (
            SemanticRetriever(vector_store, embedder, config.semantic)
            if config.semantic.enabled
            else None
        )
        self.lexical = LexicalRetriever(config.lexical) if config.lexical.enabled else None
        if self.lexical and lexical_chunks is not None:
            self.lexical.index(lexical_chunks)

        self.reranker: BaseReranker | None = None
        if config.rerank.enabled:
            self.reranker = create_reranker(config.rerank)

    def index_lexical(self, chunks: list[Chunk]) -> None:
        if not self.lexical:
            return
        self.lexical.index(chunks)

    async def retrieve(self, query: str) -> list[RetrievalResult]:
        results_by_type: dict[str, list[RetrievalResult]] = {}

        if self.semantic:
            results_by_type["semantic"] = await self.semantic.retrieve(query)

        if self.lexical:
            results_by_type["lexical"] = self.lexical.retrieve(query)

        if not results_by_type:
            return []

        fused = self._fuse_results(results_by_type)

        if self.reranker and fused:
            candidates = self.config.rerank.candidates
            to_rerank = fused[:candidates] if candidates else fused
            fused = await self.reranker.rerank(
                query,
                to_rerank,
                top_n=self.config.rerank.top_n,
                relevance_threshold=self.config.rerank.relevance_threshold,
            )

        return self._prepare_context(fused)

    def _fuse_results(self, results_by_type: dict[str, list[RetrievalResult]]) -> list[RetrievalResult]:
        if len(results_by_type) == 1:
            return next(iter(results_by_type.values()))

        weights = {
            "semantic": self.config.semantic.weight,
            "lexical": self.config.lexical.weight,
        }
        return ScoreFusion.apply(results_by_type, self.config.fusion, weights)

    def _prepare_context(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        deduped = self._deduplicate(results)
        limited = self._limit_context(deduped)
        return limited[: self.config.context.max_chunks]

    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        if not self.config.context.deduplication.enabled:
            return results
        threshold = self.config.context.deduplication.similarity_threshold
        if threshold >= 1.0:
            return results

        unique: list[RetrievalResult] = []
        for result in results:
            if not _is_similar_to_any(result.chunk.content, [r.chunk.content for r in unique], threshold):
                unique.append(result)
        return unique

    def _limit_context(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        max_tokens = self.config.context.max_tokens
        if max_tokens <= 0:
            return results
        total = 0
        limited: list[RetrievalResult] = []
        for result in results:
            tokens = _estimate_tokens(result.chunk.content)
            if total + tokens > max_tokens:
                break
            limited.append(result)
            total += tokens
        return limited


def _estimate_tokens(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _is_similar_to_any(text: str, candidates: Iterable[str], threshold: float) -> bool:
    tokens = set(_tokenize(text))
    if not tokens:
        return False
    for candidate in candidates:
        other = set(_tokenize(candidate))
        if not other:
            continue
        similarity = len(tokens & other) / max(len(tokens | other), 1)
        if similarity >= threshold:
            return True
    return False


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())
