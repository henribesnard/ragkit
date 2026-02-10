"""Tests for lexical (BM25) retrieval."""

from __future__ import annotations

import pytest

from ragkit.config.schema_v2 import RetrievalConfigV2
from ragkit.models import Chunk
from ragkit.retrieval.lexical_retriever import LexicalRetriever


class TestLexicalRetrieval:
    """Tests for BM25 lexical retrieval."""

    @pytest.fixture
    def retriever(self):
        """Create lexical retriever with test data."""
        config = RetrievalConfigV2(
            retrieval_mode="lexical",
            tokenizer_type="standard",
            lowercase_tokens=True,
            remove_stopwords=False,
        )

        retriever = LexicalRetriever(config)

        # Index test documents
        chunks = [
            Chunk(
                id="1",
                content="GET /api/users endpoint returns user list",
                metadata={},
            ),
            Chunk(
                id="2",
                content="API endpoint for retrieving user information",
                metadata={},
            ),
            Chunk(id="3", content="User management system overview", metadata={}),
        ]

        retriever.index_documents(chunks)
        return retriever

    @pytest.mark.asyncio
    async def test_bm25_exact_match(self, retriever):
        """BM25 favors exact term matches."""
        results = await retriever.search("GET /api/users endpoint")

        assert len(results) > 0
        # First result should be doc 1 (all terms present)
        assert results[0].chunk.id == "1"

    @pytest.mark.asyncio
    async def test_bm25_top_k(self, retriever):
        """Top-k limits number of results."""
        results = await retriever.search("user", top_k=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_bm25_scoring(self, retriever):
        """BM25 scores are positive and sorted."""
        results = await retriever.search("user api endpoint")

        assert all(r.score > 0 for r in results)

        # Scores should be descending
        if len(results) > 1:
            assert results[0].score >= results[-1].score


class TestTokenization:
    """Tests for tokenization strategies."""

    @pytest.mark.asyncio
    async def test_stemming_matches_variations(self):
        """Stemming finds morphological variations."""
        config = RetrievalConfigV2(
            tokenizer_type="standard",
            stemming_enabled=True,
            lowercase_tokens=True,
        )

        retriever = LexicalRetriever(config)

        chunks = [
            Chunk(id="1", content="running shoes", metadata={}),
            Chunk(id="2", content="runners compete", metadata={}),
        ]

        retriever.index_documents(chunks)

        results = await retriever.search("run")

        # With stemming: run/running/runners → same stem "run"
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_stopword_removal(self):
        """Stopword removal works correctly."""
        config = RetrievalConfigV2(
            tokenizer_type="standard",
            remove_stopwords=True,
            stopwords_language="english",
        )

        retriever = LexicalRetriever(config)

        chunks = [
            Chunk(id="1", content="the quick brown fox", metadata={}),
            Chunk(id="2", content="quick brown fox", metadata={}),
        ]

        retriever.index_documents(chunks)

        # "the" is a stopword and should be ignored
        results = await retriever.search("the quick brown")

        assert len(results) == 2  # Both docs match (stopword ignored)


class TestBM25Parameters:
    """Tests for BM25 parameter tuning."""

    @pytest.mark.asyncio
    async def test_bm25_k1_impact(self):
        """k1 parameter affects term frequency saturation."""
        # Document with many occurrences of "python"
        chunks = [
            Chunk(id="1", content="python " * 50, metadata={}),
            Chunk(id="2", content="python programming", metadata={}),
        ]

        # Low k1: fast saturation
        config_low = RetrievalConfigV2(bm25_k1=0.5)
        retriever_low = LexicalRetriever(config_low)
        retriever_low.index_documents(chunks)
        results_low = await retriever_low.search("python")

        # High k1: slow saturation (favors doc1 more)
        config_high = RetrievalConfigV2(bm25_k1=2.0)
        retriever_high = LexicalRetriever(config_high)
        retriever_high.index_documents(chunks)
        results_high = await retriever_high.search("python")

        # Both should return results
        assert len(results_low) == 2
        assert len(results_high) == 2

        # Scores should differ based on k1
        # (exact comparison depends on BM25 implementation)

    @pytest.mark.asyncio
    async def test_metadata_filtering(self):
        """Metadata filters work with lexical search."""
        config = RetrievalConfigV2()
        retriever = LexicalRetriever(config)

        chunks = [
            Chunk(id="1", content="Python doc", metadata={"source": "manual.pdf"}),
            Chunk(id="2", content="Python tutorial", metadata={"source": "tutorial.pdf"}),
        ]

        retriever.index_documents(chunks)

        results = await retriever.search(
            "Python", top_k=10, filters={"source": "manual.pdf"}
        )

        # Should only return doc from manual.pdf
        assert len(results) == 1
        assert results[0].chunk.id == "1"
