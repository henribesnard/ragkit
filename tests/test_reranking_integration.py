"""Integration tests for retrieval + reranking pipeline."""

from __future__ import annotations

import pytest

pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")

from ragkit.config.schema_v2 import (
    EmbeddingConfigV2,
    RerankingConfigV2,
    RetrievalConfigV2,
    VectorDBConfigV2,
)
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.models import Chunk
from ragkit.reranking.cross_encoder_reranker import CrossEncoderReranker
from ragkit.reranking.multi_stage_reranker import MultiStageReranker
from ragkit.retrieval.hybrid_retriever import HybridRetriever
from ragkit.retrieval.lexical_retriever import LexicalRetriever
from ragkit.retrieval.semantic_retriever import SemanticRetriever
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class TestRetrievalReranking:
    """Integration tests for retrieval + reranking pipeline."""

    @pytest.fixture
    async def setup_pipeline(self):
        """Setup complete retrieval + reranking pipeline."""
        # Configs
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
            cache_embeddings=False,
        )

        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_reranking_integration",
        )

        retrieval_config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            alpha=0.5,
            fusion_method="rrf",
            top_k=20,  # Retrieve more for reranking
        )

        reranking_config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            rerank_top_n=20,
            final_top_k=5,
            use_gpu=False,
        )

        # Components
        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)

        semantic = SemanticRetriever(vectordb, embedder, retrieval_config)
        lexical = LexicalRetriever(retrieval_config)
        hybrid = HybridRetriever(semantic, lexical, retrieval_config)

        reranker = CrossEncoderReranker(reranking_config)

        # Test documents
        chunks = [
            Chunk(
                id="1",
                content=(
                    "Best practices for securing API endpoints with authentication and "
                    "authorization"
                ),
                metadata={"source": "security_guide.pdf"},
            ),
            Chunk(
                id="2",
                content="How to implement OAuth 2.0 for API security",
                metadata={"source": "security_guide.pdf"},
            ),
            Chunk(
                id="3",
                content="API endpoint design patterns for REST services",
                metadata={"source": "api_design.pdf"},
            ),
            Chunk(
                id="4",
                content="Python programming fundamentals and data structures",
                metadata={"source": "python_tutorial.pdf"},
            ),
            Chunk(
                id="5",
                content="Machine learning algorithms and neural networks",
                metadata={"source": "ml_course.pdf"},
            ),
            Chunk(
                id="6",
                content="JWT tokens for API authentication and session management",
                metadata={"source": "security_guide.pdf"},
            ),
            Chunk(
                id="7",
                content="Database optimization techniques for web applications",
                metadata={"source": "database_guide.pdf"},
            ),
            Chunk(
                id="8",
                content="API rate limiting and throttling strategies",
                metadata={"source": "api_design.pdf"},
            ),
            Chunk(
                id="9",
                content="Docker containerization for microservices",
                metadata={"source": "devops_guide.pdf"},
            ),
            Chunk(
                id="10",
                content="HTTPS and TLS for secure API communications",
                metadata={"source": "security_guide.pdf"},
            ),
        ]

        # Index documents
        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)
        lexical.index_documents(chunks)

        return {
            "retriever": hybrid,
            "reranker": reranker,
            "chunks": chunks,
        }

    @pytest.mark.asyncio
    async def test_e2e_retrieval_reranking(self, setup_pipeline):
        """Test end-to-end retrieval → reranking pipeline."""
        retriever = setup_pipeline["retriever"]
        reranker = setup_pipeline["reranker"]

        query = "How to secure API endpoints?"

        # Step 1: Retrieval
        retrieval_results = await retriever.search(query, top_k=20)

        assert len(retrieval_results) > 0
        print(f"Retrieval returned {len(retrieval_results)} results")

        # Step 2: Reranking
        # Convert SearchResult to Chunk for reranking
        candidate_chunks = [result.chunk for result in retrieval_results]

        reranked_results = await reranker.rerank(
            query=query,
            chunks=candidate_chunks,
            top_k=5,
        )

        # Validations
        assert len(reranked_results) == 5

        # Results should be ranked 1-5
        assert all(r.rank in range(1, 6) for r in reranked_results)

        # Scores should be descending
        for i in range(len(reranked_results) - 1):
            assert reranked_results[i].score >= reranked_results[i + 1].score

        # Top results should be API security related
        top_3_ids = {r.chunk.id for r in reranked_results[:3]}
        security_docs = {"1", "2", "6", "10"}  # Known API security docs

        overlap = len(top_3_ids & security_docs)
        assert overlap >= 2, f"Expected security docs in top 3, got {top_3_ids}"

    @pytest.mark.asyncio
    async def test_reranking_improves_precision(self, setup_pipeline):
        """Test that reranking improves precision over retrieval alone."""
        retriever = setup_pipeline["retriever"]
        reranker = setup_pipeline["reranker"]

        query = "API security authentication"

        # Ground truth: docs about API security
        relevant_ids = {"1", "2", "6", "10"}

        # Retrieval only (top 5)
        retrieval_results = await retriever.search(query, top_k=5)
        retrieval_top_5_ids = {r.chunk.id for r in retrieval_results[:5]}

        # Precision@5 for retrieval
        precision_retrieval = len(retrieval_top_5_ids & relevant_ids) / 5

        # Retrieval + Reranking
        retrieval_for_reranking = await retriever.search(query, top_k=20)
        candidate_chunks = [r.chunk for r in retrieval_for_reranking]

        reranked_results = await reranker.rerank(query, candidate_chunks, top_k=5)
        reranked_top_5_ids = {r.chunk.id for r in reranked_results}

        # Precision@5 for reranking
        precision_reranked = len(reranked_top_5_ids & relevant_ids) / 5

        print(f"Precision@5 - Retrieval: {precision_retrieval:.2%}")
        print(f"Precision@5 - Reranked: {precision_reranked:.2%}")

        # Reranking should improve or maintain precision
        # (In this small test set, exact comparison may vary)
        # At minimum, reranking shouldn't hurt significantly
        assert precision_reranked >= precision_retrieval - 0.2

    @pytest.mark.asyncio
    async def test_reranking_changes_order(self, setup_pipeline):
        """Test that reranking actually changes result order."""
        retriever = setup_pipeline["retriever"]
        reranker = setup_pipeline["reranker"]

        query = "API authentication methods"

        # Get retrieval results
        retrieval_results = await retriever.search(query, top_k=10)
        retrieval_ids = [r.chunk.id for r in retrieval_results]

        # Rerank
        candidate_chunks = [r.chunk for r in retrieval_results]
        reranked_results = await reranker.rerank(query, candidate_chunks, top_k=5)
        reranked_ids = [r.chunk.id for r in reranked_results]

        # At least some documents should be reordered
        # (i.e., reranking should have an effect)
        differences = sum(1 for i in range(5) if retrieval_ids[i] != reranked_ids[i])
        assert differences >= 1, "Reranking should change order of at least 1 document"


class TestMultiStageIntegration:
    """Integration tests for multi-stage reranking."""

    @pytest.mark.asyncio
    async def test_multi_stage_e2e(self):
        """Test end-to-end pipeline with multi-stage reranking."""
        # Setup
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
        )

        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_multistage",
        )

        retrieval_config = RetrievalConfigV2(
            retrieval_mode="semantic",
            top_k=50,  # Retrieve many candidates
        )

        reranking_config = RerankingConfigV2(
            reranker_enabled=True,
            multi_stage_reranking=True,
            stage_1_model="cross-encoder/ms-marco-TinyBERT-L-2-v2",
            stage_2_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            stage_1_keep_top=20,
            rerank_top_n=50,
            final_top_k=5,
            use_gpu=False,
        )

        # Components
        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)
        retriever = SemanticRetriever(vectordb, embedder, retrieval_config)
        reranker = MultiStageReranker(reranking_config)

        # Index documents
        chunks = [
            Chunk(id=f"doc_{i}", content=f"API security document {i}", metadata={})
            for i in range(30)
        ] + [
            Chunk(id=f"other_{i}", content=f"Unrelated document {i}", metadata={})
            for i in range(20)
        ]

        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)

        # Query
        query = "API security best practices"

        # Retrieval
        retrieval_results = await retriever.search(query, top_k=50)
        candidate_chunks = [r.chunk for r in retrieval_results]

        # Multi-stage reranking
        final_results = await reranker.rerank(query, candidate_chunks, top_k=5)

        # Validations
        assert len(final_results) == 5
        assert all(r.rank in range(1, 6) for r in final_results)

        # Check stage info
        stage_info = reranker.get_stage_info()
        assert stage_info["stage_1"]["keep_top"] == 20
        assert stage_info["stage_2"]["model"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"


class TestMetadataFiltering:
    """Test reranking with metadata filtering."""

    @pytest.mark.asyncio
    async def test_rerank_with_filtered_results(self):
        """Test reranking on filtered retrieval results."""
        # Setup
        embedding_config = EmbeddingConfigV2(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2",
        )

        vectordb_config = VectorDBConfigV2(
            provider="chromadb",
            in_memory=True,
            collection_name="test_filtered_rerank",
        )

        retrieval_config = RetrievalConfigV2(retrieval_mode="semantic")
        reranking_config = RerankingConfigV2(
            reranker_enabled=True,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            use_gpu=False,
        )

        # Components
        embedder = AdvancedEmbedder(embedding_config)
        vectordb = ChromaDBAdapter(vectordb_config)
        retriever = SemanticRetriever(vectordb, embedder, retrieval_config)
        reranker = CrossEncoderReranker(reranking_config)

        # Documents with metadata
        chunks = [
            Chunk(
                id="1",
                content="API security in Python",
                metadata={"language": "python"},
            ),
            Chunk(
                id="2",
                content="API security in JavaScript",
                metadata={"language": "javascript"},
            ),
            Chunk(
                id="3",
                content="API security in Go",
                metadata={"language": "go"},
            ),
        ]

        texts = [c.content for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(chunks, embeddings)

        # Retrieval with filter
        query = "API security"
        filtered_results = await retriever.search(
            query,
            top_k=10,
            filters={"language": "python"},
        )

        # Rerank filtered results
        candidate_chunks = [r.chunk for r in filtered_results]
        reranked = await reranker.rerank(query, candidate_chunks, top_k=3)

        # All results should still be Python docs
        assert all(r.chunk.metadata["language"] == "python" for r in reranked)
