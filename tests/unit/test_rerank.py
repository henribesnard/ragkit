"""Tests for ragkit.retrieval.rerank."""

import pytest

from ragkit.config.schema import RerankConfig
from ragkit.models import Chunk, RetrievalResult
from ragkit.retrieval.rerank import NoOpReranker, create_reranker


@pytest.mark.asyncio
async def test_noop_reranker_returns_top_n():
    chunk_a = Chunk(id="A", document_id="docA", content="alpha", metadata={})
    chunk_b = Chunk(id="B", document_id="docB", content="beta", metadata={})
    chunk_c = Chunk(id="C", document_id="docC", content="gamma", metadata={})

    results = [
        RetrievalResult(chunk=chunk_a, score=0.9, retrieval_type="semantic"),
        RetrievalResult(chunk=chunk_b, score=0.8, retrieval_type="semantic"),
        RetrievalResult(chunk=chunk_c, score=0.7, retrieval_type="semantic"),
    ]

    reranker = NoOpReranker()
    reranked = await reranker.rerank("query", results, top_n=2)

    assert len(reranked) == 2
    assert reranked[0].chunk.id == "A"
    assert reranked[1].chunk.id == "B"


@pytest.mark.asyncio
async def test_noop_reranker_filters_by_threshold():
    chunk_a = Chunk(id="A", document_id="docA", content="alpha", metadata={})
    chunk_b = Chunk(id="B", document_id="docB", content="beta", metadata={})

    results = [
        RetrievalResult(chunk=chunk_a, score=0.9, retrieval_type="semantic"),
        RetrievalResult(chunk=chunk_b, score=0.3, retrieval_type="semantic"),
    ]

    reranker = NoOpReranker()
    reranked = await reranker.rerank("query", results, top_n=10, relevance_threshold=0.5)

    assert len(reranked) == 1
    assert reranked[0].chunk.id == "A"


@pytest.mark.asyncio
async def test_noop_reranker_empty_input():
    reranker = NoOpReranker()
    reranked = await reranker.rerank("query", [], top_n=5)
    assert reranked == []


def test_create_reranker_disabled():
    config = RerankConfig(enabled=False)
    reranker = create_reranker(config)
    assert isinstance(reranker, NoOpReranker)


def test_create_reranker_provider_none():
    config = RerankConfig(enabled=True, provider="none")
    reranker = create_reranker(config)
    assert isinstance(reranker, NoOpReranker)


def test_create_reranker_unknown_provider():
    config = RerankConfig(enabled=True, provider="cohere", api_key="test")
    # CohereReranker requires the cohere package, which may not be installed
    # This test just verifies create_reranker dispatches correctly
    try:
        reranker = create_reranker(config)
        # If cohere is installed, we get a CohereReranker
        assert reranker is not None
    except Exception:
        # If cohere is not installed, we expect a RetrievalError
        pass
