"""Shared test doubles and helpers used across test modules."""

from __future__ import annotations

import types
from typing import Any

from ragkit.embedding.base import BaseEmbedder
from ragkit.models import Chunk, GeneratedResponse, QueryAnalysis, RetrievalResult
from ragkit.vectorstore.base import BaseVectorStore, SearchResult, VectorStoreStats

# ---------------------------------------------------------------------------
# LLM test doubles
# ---------------------------------------------------------------------------


class DummyLLM:
    """Fake LLM provider that returns canned responses."""

    def __init__(self, json_response: dict[str, Any] | None = None, text_response: str = "ok"):
        self.json_response = json_response or {}
        self.text_response = text_response
        self.call_count = 0

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        return self.text_response

    async def complete_json(
        self, messages: list[dict[str, str]], schema: dict[str, Any]
    ) -> dict[str, Any]:
        self.call_count += 1
        return self.json_response


class DummyChoice:
    def __init__(self, content: str):
        self.message = types.SimpleNamespace(content=content)


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


# ---------------------------------------------------------------------------
# Embedding test doubles
# ---------------------------------------------------------------------------


class DummyEmbedder(BaseEmbedder):
    """Fake embedder returning fixed vectors."""

    def __init__(self) -> None:
        self.call_count = 0

    @property
    def dimensions(self) -> int:
        return 3

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        self.call_count += 1
        return [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Vector store test doubles
# ---------------------------------------------------------------------------


class DummyVectorStore(BaseVectorStore):
    """In-memory vector store that returns preconfigured results."""

    def __init__(self, results: list[SearchResult] | None = None):
        self._results: list[SearchResult] = results or []

    async def add(self, chunks: list[Chunk]) -> None:
        return None

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        return self._results[:top_k]

    async def delete(self, ids: list[str]) -> None:
        return None

    async def clear(self) -> None:
        return None

    async def count(self) -> int:
        return len(self._results)

    async def stats(self) -> VectorStoreStats:
        return VectorStoreStats(
            provider="dummy", collection_name="dummy", vector_count=len(self._results)
        )

    async def list_documents(self) -> list[str]:
        return []

    async def list_chunks(self) -> list[Chunk]:
        return [result.chunk for result in self._results]


# ---------------------------------------------------------------------------
# Retrieval / orchestrator test doubles
# ---------------------------------------------------------------------------


class DummyRetrieval:
    """Fake retrieval engine returning a single result."""

    async def retrieve(self, query: str) -> list[RetrievalResult]:
        chunk = Chunk(
            id="1", document_id="doc1", content="Paris is capital", metadata={"source": "geo.pdf"}
        )
        return [RetrievalResult(chunk=chunk, score=0.9, retrieval_type="semantic")]


class DummyRouter:
    """Fake LLM router that returns the same LLM for any reference."""

    def __init__(self, llm: DummyLLM):
        self.llm = llm

    def get(self, model_ref: str) -> DummyLLM:
        return self.llm


class DummyOrchestrator:
    """Fake orchestrator for API tests."""

    async def process(self, query: str, history: list[dict[str, str]] | None = None) -> Any:
        analysis = QueryAnalysis(intent="question", needs_retrieval=True)
        chunk = Chunk(id="1", document_id="doc", content="Hello", metadata={"source": "doc"})
        context = [RetrievalResult(chunk=chunk, score=0.9, retrieval_type="semantic")]
        response = GeneratedResponse(content="Answer", sources=["doc"], metadata={})
        return types.SimpleNamespace(response=response, analysis=analysis, context=context)

    async def process_stream(self, query: str, history: list[dict[str, str]] | None = None) -> Any:
        yield {"type": "delta", "content": "Answer"}
        yield {
            "type": "final",
            "content": "Answer",
            "sources": ["doc"],
            "metadata": {"intent": "question"},
        }


# ---------------------------------------------------------------------------
# Common test data factories
# ---------------------------------------------------------------------------


def make_chunk(
    id: str = "1",
    document_id: str = "doc1",
    content: str = "test content",
    metadata: dict[str, Any] | None = None,
) -> Chunk:
    return Chunk(id=id, document_id=document_id, content=content, metadata=metadata or {})


def make_retrieval_result(
    chunk: Chunk | None = None,
    score: float = 0.9,
    retrieval_type: str = "semantic",
) -> RetrievalResult:
    if chunk is None:
        chunk = make_chunk()
    return RetrievalResult(chunk=chunk, score=score, retrieval_type=retrieval_type)
