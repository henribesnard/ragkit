"""Semantic retrieval implementation."""

from __future__ import annotations

from ragkit.config.schema import SemanticRetrievalConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.models import RetrievalResult
from ragkit.vectorstore.base import BaseVectorStore


class SemanticRetriever:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: BaseEmbedder,
        config: SemanticRetrievalConfig,
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = config.top_k
        self.threshold = config.similarity_threshold

    async def retrieve(self, query: str) -> list[RetrievalResult]:
        query_embedding = await self.embedder.embed_query(query)
        results = await self.vector_store.search(query_embedding, self.top_k)

        filtered = [result for result in results if result.score >= self.threshold]
        filtered.sort(key=lambda item: item.score, reverse=True)

        return [
            RetrievalResult(chunk=result.chunk, score=result.score, retrieval_type="semantic")
            for result in filtered
        ]
