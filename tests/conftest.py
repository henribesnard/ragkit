"""Shared pytest fixtures available to all test modules."""

import pytest

from ragkit.vectorstore.base import SearchResult
from tests.helpers import (
    DummyEmbedder,
    DummyLLM,
    DummyRetrieval,
    DummyVectorStore,
    make_chunk,
)


@pytest.fixture
def dummy_llm():
    return DummyLLM()


@pytest.fixture
def dummy_embedder():
    return DummyEmbedder()


@pytest.fixture
def dummy_vector_store():
    return DummyVectorStore()


@pytest.fixture
def dummy_retrieval():
    return DummyRetrieval()


@pytest.fixture
def sample_chunk():
    return make_chunk(
        id="1", document_id="doc1", content="Paris is capital", metadata={"source": "geo.pdf"}
    )


@pytest.fixture
def sample_chunks():
    return [
        make_chunk(id="A", document_id="docA", content="alpha beta", metadata={}),
        make_chunk(id="B", document_id="docB", content="beta gamma", metadata={}),
        make_chunk(id="C", document_id="docC", content="gamma delta", metadata={}),
    ]


@pytest.fixture
def sample_search_results(sample_chunks):
    return [SearchResult(chunk=c, score=0.9 - i * 0.1) for i, c in enumerate(sample_chunks)]


@pytest.fixture
def sample_docs(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("# Doc 1\nParis is the capital of France.")
    (docs_dir / "doc2.txt").write_text("This document talks about machine learning.")
    return docs_dir
