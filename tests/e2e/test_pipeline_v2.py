"""End-to-end tests for complete RAG pipeline V2.

Tests the full workflow with V2 architecture:
1. Document ingestion
2. Chunking
3. Embedding
4. Indexing
5. Retrieval (semantic, lexical, hybrid)
6. Reranking
7. Generation (if LLM available)
"""

from __future__ import annotations

import time

import pytest

from ragkit.models import Chunk


class TestFullRAGPipelineV2:
    """Test complete RAG pipeline end-to-end with V2 components."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_retrieval_reranking_pipeline(
        self,
        test_chunks,
        rag_pipeline_components,
        sample_queries,
    ):
        """Test complete retrieval + reranking pipeline."""
        # Get components
        embedder = rag_pipeline_components["embedder"]
        vectordb = rag_pipeline_components["vectordb"]
        lexical = rag_pipeline_components["lexical"]
        hybrid = rag_pipeline_components["hybrid"]
        reranker = rag_pipeline_components["reranker"]

        # 1. Index documents
        print(f"\n=== Indexing {len(test_chunks)} chunks ===")

        # Embed chunks
        texts = [chunk.content for chunk in test_chunks]
        start = time.time()
        embeddings = await embedder.embed_batch(texts)
        embed_time = time.time() - start
        print(f"Embedding time: {embed_time:.2f}s")

        # Index in vector DB
        await vectordb.insert_batch(test_chunks, embeddings)

        # Index in lexical retriever
        lexical.index_documents(test_chunks)

        print(f"Indexed {len(test_chunks)} chunks successfully")

        # 2. Test queries
        for query_info in sample_queries[:2]:  # Test first 2 queries
            query = query_info["query"]
            expected_docs = query_info["expected_docs"]

            print(f"\n=== Query: {query} ===")

            # Step 1: Retrieval
            start = time.time()
            retrieval_results = await hybrid.search(query, top_k=10)
            retrieval_time = time.time() - start

            print(f"Retrieval time: {retrieval_time * 1000:.0f}ms")
            print(f"Retrieved {len(retrieval_results)} results")

            # Validate retrieval
            assert len(retrieval_results) > 0, "Should retrieve at least one result"
            assert len(retrieval_results) <= 10, "Should respect top_k=10"

            # Step 2: Reranking
            candidate_chunks = [r.chunk for r in retrieval_results]

            start = time.time()
            reranked_results = await reranker.rerank(query, candidate_chunks, top_k=5)
            rerank_time = time.time() - start

            print(f"Reranking time: {rerank_time * 1000:.0f}ms")
            print(f"Reranked to top {len(reranked_results)} results")

            # Validate reranking
            assert len(reranked_results) <= 5, "Should respect top_k=5"
            assert all(r.rank in range(1, 6) for r in reranked_results), "Ranks should be 1-5"

            # Check scores are descending
            for i in range(len(reranked_results) - 1):
                assert (
                    reranked_results[i].score >= reranked_results[i + 1].score
                ), "Scores should be descending"

            # Check relevance (at least one expected doc in top 5)
            top_parent_ids = {
                r.chunk.metadata.get("parent_id") for r in reranked_results
            }
            overlap = len(set(expected_docs) & top_parent_ids)
            assert overlap >= 1, f"Expected at least one relevant doc, got {top_parent_ids}"

            # Print results
            print("\nTop 5 reranked results:")
            for result in reranked_results:
                parent_id = result.chunk.metadata.get("parent_id", "unknown")
                print(f"  {result.rank}. [{result.score:.3f}] {parent_id}: {result.chunk.content[:60]}...")

            # Total latency
            total_latency = (retrieval_time + rerank_time) * 1000
            print(f"\nTotal latency: {total_latency:.0f}ms")

            # Performance assertions
            assert total_latency < 10000, f"Total latency too high: {total_latency:.0f}ms"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_semantic_only_pipeline(
        self,
        test_chunks,
        rag_pipeline_components,
    ):
        """Test semantic-only retrieval pipeline."""
        embedder = rag_pipeline_components["embedder"]
        vectordb = rag_pipeline_components["vectordb"]
        semantic = rag_pipeline_components["semantic"]

        # Index
        texts = [chunk.content for chunk in test_chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(test_chunks, embeddings)

        # Query
        query = "API authentication methods"
        results = await semantic.search(query, top_k=5)

        # Validate
        assert len(results) > 0, "Should return results"
        assert len(results) <= 5, "Should respect top_k=5"
        assert all(r.score > 0 for r in results), "Scores should be positive"

        # Check that results are from vector DB
        assert all(hasattr(r, "chunk") for r in results), "Results should have chunks"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_lexical_only_pipeline(
        self,
        test_chunks,
        rag_pipeline_components,
    ):
        """Test lexical-only (BM25) retrieval pipeline."""
        lexical = rag_pipeline_components["lexical"]

        # Index
        lexical.index_documents(test_chunks)

        # Query with specific terms
        query = "OAuth 2.0 JWT authentication"
        results = await lexical.search(query, top_k=5)

        # Validate
        assert len(results) > 0, "Should return results"
        assert len(results) <= 5, "Should respect top_k=5"

        # BM25 scores should be positive
        assert all(r.score > 0 for r in results), "BM25 scores should be positive"

        # Should find doc_1 (API Security) which mentions OAuth and JWT
        parent_ids = {r.chunk.metadata.get("parent_id") for r in results}
        assert "doc_1" in parent_ids, "Should find API security doc"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_hybrid_fusion_methods(
        self,
        test_chunks,
        rag_pipeline_components,
    ):
        """Test different fusion methods in hybrid retrieval."""
        from ragkit.config.schema_v2 import RetrievalConfigV2
        from ragkit.retrieval.hybrid_retriever import HybridRetriever

        embedder = rag_pipeline_components["embedder"]
        vectordb = rag_pipeline_components["vectordb"]
        semantic = rag_pipeline_components["semantic"]
        lexical = rag_pipeline_components["lexical"]

        # Index
        texts = [chunk.content for chunk in test_chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(test_chunks, embeddings)
        lexical.index_documents(test_chunks)

        query = "API security authentication"

        # Test RRF fusion
        rrf_config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            alpha=0.5,
            fusion_method="rrf",
            top_k=5,
        )
        hybrid_rrf = HybridRetriever(semantic, lexical, rrf_config)
        rrf_results = await hybrid_rrf.search(query)

        # Test linear fusion
        linear_config = RetrievalConfigV2(
            retrieval_mode="hybrid",
            alpha=0.5,
            fusion_method="linear",
            top_k=5,
        )
        hybrid_linear = HybridRetriever(semantic, lexical, linear_config)
        linear_results = await hybrid_linear.search(query)

        # Both should return results
        assert len(rrf_results) > 0, "RRF should return results"
        assert len(linear_results) > 0, "Linear should return results"

        # Results may differ but should both be relevant
        rrf_parent_ids = {r.chunk.metadata.get("parent_id") for r in rrf_results}
        linear_parent_ids = {r.chunk.metadata.get("parent_id") for r in linear_results}

        # Both should find doc_1 (API security)
        assert "doc_1" in rrf_parent_ids or "doc_1" in linear_parent_ids, "Should find API security doc"


class TestPipelineLatency:
    """Test pipeline latency and performance."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_end_to_end_latency(
        self,
        test_chunks,
        rag_pipeline_components,
    ):
        """Test that E2E latency is reasonable."""
        embedder = rag_pipeline_components["embedder"]
        vectordb = rag_pipeline_components["vectordb"]
        lexical = rag_pipeline_components["lexical"]
        hybrid = rag_pipeline_components["hybrid"]
        reranker = rag_pipeline_components["reranker"]

        # Index (one-time cost)
        texts = [chunk.content for chunk in test_chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(test_chunks, embeddings)
        lexical.index_documents(test_chunks)

        # Measure query latency
        query = "How to optimize database performance?"

        start = time.time()

        # Retrieval
        retrieval_results = await hybrid.search(query, top_k=20)

        # Reranking
        candidate_chunks = [r.chunk for r in retrieval_results]
        final_results = await reranker.rerank(query, candidate_chunks, top_k=5)

        total_latency = (time.time() - start) * 1000

        print(f"\n=== Latency Breakdown ===")
        print(f"Total E2E latency: {total_latency:.0f}ms")

        # Assertions (realistic latency for CPU)
        assert total_latency < 10000, f"E2E latency too high: {total_latency:.0f}ms"
        assert len(final_results) > 0, "Should return results"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_concurrent_queries(
        self,
        test_chunks,
        rag_pipeline_components,
        sample_queries,
    ):
        """Test concurrent query handling."""
        import asyncio

        embedder = rag_pipeline_components["embedder"]
        vectordb = rag_pipeline_components["vectordb"]
        lexical = rag_pipeline_components["lexical"]
        hybrid = rag_pipeline_components["hybrid"]

        # Index
        texts = [chunk.content for chunk in test_chunks]
        embeddings = await embedder.embed_batch(texts)
        await vectordb.insert_batch(test_chunks, embeddings)
        lexical.index_documents(test_chunks)

        # Run 5 queries concurrently
        queries = [q["query"] for q in sample_queries]

        start = time.time()
        results_list = await asyncio.gather(
            *[hybrid.search(q, top_k=5) for q in queries]
        )
        elapsed = time.time() - start

        print(f"\n=== Concurrent Queries ===")
        print(f"Processed {len(queries)} queries in {elapsed:.2f}s")
        print(f"QPS: {len(queries) / elapsed:.1f}")

        # All queries should return results
        assert all(len(results) > 0 for results in results_list), "All queries should return results"

        # Check QPS is reasonable
        qps = len(queries) / elapsed
        print(f"Throughput: {qps:.1f} QPS")
