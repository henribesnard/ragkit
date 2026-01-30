import pytest

from ragkit.config.schema import (
    FusionConfig,
    LexicalPreprocessingConfig,
    LexicalRetrievalConfig,
    RetrievalConfig,
    SemanticRetrievalConfig,
)
from ragkit.embedding.base import BaseEmbedder
from ragkit.models import Chunk, RetrievalResult
from ragkit.retrieval.engine import RetrievalEngine
from ragkit.retrieval.fusion import ScoreFusion
from ragkit.retrieval.lexical import LexicalRetriever
from ragkit.retrieval.semantic import SemanticRetriever
from ragkit.vectorstore.base import BaseVectorStore, SearchResult


class DummyEmbedder(BaseEmbedder):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    @property
    def dimensions(self):
        return 3


class DummyVectorStore(BaseVectorStore):
    def __init__(self, results: list[SearchResult]):
        self._results = results

    async def add(self, chunks: list[Chunk]) -> None:
        return None

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        return self._results[:top_k]

    async def delete(self, ids: list[str]) -> None:
        return None

    async def clear(self) -> None:
        return None


@pytest.mark.asyncio
async def test_semantic_retrieval():
    chunk_a = Chunk(id="A", document_id="docA", content="alpha", metadata={})
    chunk_b = Chunk(id="B", document_id="docB", content="beta", metadata={})
    results = [
        SearchResult(chunk=chunk_b, score=0.4),
        SearchResult(chunk=chunk_a, score=0.9),
    ]
    store = DummyVectorStore(results)
    embedder = DummyEmbedder()
    config = SemanticRetrievalConfig(enabled=True, top_k=5, similarity_threshold=0.5)

    retriever = SemanticRetriever(store, embedder, config)
    retrieved = await retriever.retrieve("query")

    assert len(retrieved) == 1
    assert retrieved[0].chunk.id == "A"
    assert retrieved[0].retrieval_type == "semantic"


def test_lexical_retrieval():
    config = LexicalRetrievalConfig(
        enabled=True,
        top_k=5,
        preprocessing=LexicalPreprocessingConfig(lowercase=True, remove_stopwords=True),
    )
    retriever = LexicalRetriever(config)

    chunks = [
        Chunk(id="1", document_id="doc1", content="Python programming language tutorial", metadata={}),
        Chunk(id="2", document_id="doc2", content="Java development best practices", metadata={}),
        Chunk(id="3", document_id="doc3", content="Python machine learning guide", metadata={}),
    ]
    retriever.index(chunks)
    results = retriever.retrieve("Python programming")

    assert results
    assert "Python" in results[0].chunk.content


def test_rrf_fusion():
    chunk_a = Chunk(id="A", document_id="docA", content="a", metadata={})
    chunk_b = Chunk(id="B", document_id="docB", content="b", metadata={})
    chunk_c = Chunk(id="C", document_id="docC", content="c", metadata={})

    semantic_results = [
        RetrievalResult(chunk=chunk_a, score=0.9, retrieval_type="semantic"),
        RetrievalResult(chunk=chunk_b, score=0.8, retrieval_type="semantic"),
    ]
    lexical_results = [
        RetrievalResult(chunk=chunk_b, score=0.95, retrieval_type="lexical"),
        RetrievalResult(chunk=chunk_c, score=0.85, retrieval_type="lexical"),
    ]

    fused = ScoreFusion.reciprocal_rank_fusion(
        {"semantic": semantic_results, "lexical": lexical_results},
        k=60,
    )
    ids = [result.chunk.id for result in fused]
    assert "B" in ids[:2]


@pytest.mark.asyncio
async def test_retrieval_engine_hybrid():
    chunk_a = Chunk(id="A", document_id="docA", content="alpha beta", metadata={})
    chunk_b = Chunk(id="B", document_id="docB", content="beta gamma", metadata={})

    semantic_results = [
        SearchResult(chunk=chunk_b, score=0.6),
        SearchResult(chunk=chunk_a, score=0.9),
    ]
    store = DummyVectorStore(semantic_results)
    embedder = DummyEmbedder()

    config = RetrievalConfig(
        architecture="hybrid",
        semantic=SemanticRetrievalConfig(enabled=True, weight=0.5, top_k=5),
        lexical=LexicalRetrievalConfig(enabled=True, weight=0.5, top_k=5),
        fusion=FusionConfig(method="weighted_sum", normalize_scores=True, rrf_k=60),
    )

    engine = RetrievalEngine(config, store, embedder, lexical_chunks=[chunk_a, chunk_b])
    results = await engine.retrieve("alpha")

    assert results
    assert results[0].chunk.id in {"A", "B"}
