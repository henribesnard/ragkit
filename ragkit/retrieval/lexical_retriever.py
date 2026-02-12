"""Lexical retriever using BM25 sparse retrieval."""

from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi, BM25Plus

from ragkit.config.schema_v2 import RetrievalConfigV2
from ragkit.models import Chunk
from ragkit.retrieval.base_retriever import BaseRetriever, SearchResult
from ragkit.retrieval.utils.tokenizers import create_tokenizer


class LexicalRetriever(BaseRetriever):
    """Lexical retrieval using BM25 algorithm.

    Features:
    - BM25/BM25+ scoring
    - Configurable tokenization (standard, whitespace, ngram)
    - Stemming/lemmatization support
    - Stopword removal
    """

    def __init__(self, config: RetrievalConfigV2) -> None:
        """Initialize lexical retriever.

        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.tokenizer = create_tokenizer(config)
        self.bm25: BM25Okapi | BM25Plus | None = None
        self.chunks: list[Chunk] = []
        self.tokenized_docs: list[list[str]] = []

    def index_documents(self, chunks: list[Chunk]) -> None:
        """Index documents for BM25 search.

        Args:
            chunks: List of chunks to index
        """
        if not chunks:
            return

        self.chunks = chunks

        # Tokenize all documents
        self.tokenized_docs = [self.tokenizer.tokenize(chunk.content) for chunk in chunks]

        # Create BM25 index
        if self.config.bm25_delta > 0:
            # Use BM25+ (improved for short documents)
            self.bm25 = BM25Plus(
                self.tokenized_docs,
                k1=self.config.bm25_k1,
                b=self.config.bm25_b,
                delta=self.config.bm25_delta,
            )
        else:
            # Use standard BM25
            self.bm25 = BM25Okapi(
                self.tokenized_docs,
                k1=self.config.bm25_k1,
                b=self.config.bm25_b,
            )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search using BM25 lexical matching.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult, sorted by BM25 score
        """
        if self.bm25 is None or not self.chunks:
            return []

        # 1. Tokenize query
        tokenized_query = self.tokenizer.tokenize(query)

        if not tokenized_query:
            return []

        # 2. BM25 scoring
        scores = self.bm25.get_scores(tokenized_query)

        # 3. Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # 4. Create search results
        results = [
            SearchResult(
                chunk=self.chunks[i],
                score=float(scores[i]),
                metadata=self.chunks[i].metadata,
            )
            for i in top_indices
            if scores[i] > 0  # Only include documents with positive scores
        ]

        # 5. Apply metadata filters if provided
        if filters:
            results = self._apply_filters(results, filters)

        # 6. Apply score threshold
        if self.config.score_threshold > 0:
            results = [r for r in results if r.score >= self.config.score_threshold]

        return results[:top_k]

    def _apply_filters(
        self,
        results: list[SearchResult],
        filters: dict[str, object],
    ) -> list[SearchResult]:
        """Apply metadata filters to results.

        Args:
            results: List of search results
            filters: Metadata filters

        Returns:
            Filtered results
        """
        filtered = []

        for result in results:
            # Check if all filter conditions match
            match = True
            for key, value in filters.items():
                if key not in result.metadata or result.metadata[key] != value:
                    match = False
                    break

            if match:
                filtered.append(result)

        return filtered
