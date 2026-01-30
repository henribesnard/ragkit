"""Reranking utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ragkit.config.schema import RerankConfig
from ragkit.exceptions import RetrievalError
from ragkit.models import RetrievalResult


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_n: int,
        relevance_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """Rerank retrieval results."""


class NoOpReranker(BaseReranker):
    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_n: int,
        relevance_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        filtered = [result for result in results if result.score >= relevance_threshold]
        return filtered[:top_n]


class CohereReranker(BaseReranker):
    def __init__(self, config: RerankConfig) -> None:
        try:
            import cohere
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError("cohere is required for reranking") from exc

        if not config.api_key:
            raise RetrievalError("Cohere API key is required for reranking")
        self.client = cohere.AsyncClient(api_key=config.api_key)
        self.model = config.model

    async def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_n: int,
        relevance_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        if not results:
            return []
        documents = [result.chunk.content for result in results]
        response = await self.client.rerank(
            query=query,
            documents=documents,
            model=self.model,
            top_n=top_n,
        )

        reranked: list[RetrievalResult] = []
        for item in response.results:
            original = results[item.index]
            score = float(item.relevance_score)
            if score < relevance_threshold:
                continue
            reranked.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=score,
                    retrieval_type="rerank",
                )
            )
        return reranked


def create_reranker(config: RerankConfig) -> BaseReranker:
    if not config.enabled or config.provider == "none":
        return NoOpReranker()
    if config.provider == "cohere":
        return CohereReranker(config)
    raise ValueError(f"Unknown rerank provider: {config.provider}")
