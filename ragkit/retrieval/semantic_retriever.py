"""Semantic retriever using dense vector search."""

from __future__ import annotations

from ragkit.config.schema_v2 import RetrievalConfigV2
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.models import Chunk
from ragkit.retrieval.base_retriever import BaseRetriever, SearchResult
from ragkit.retrieval.mmr import maximal_marginal_relevance
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


class SemanticRetriever(BaseRetriever):
    """Semantic retrieval using vector similarity search.

    Features:
    - Dense vector search via VectorDB
    - MMR for diversity (optional)
    - Metadata filtering
    - Score thresholding
    """

    def __init__(
        self,
        vectordb: ChromaDBAdapter,
        embedder: AdvancedEmbedder,
        config: RetrievalConfigV2,
    ):
        """Initialize semantic retriever.

        Args:
            vectordb: Vector database adapter
            embedder: Embedding model
            config: Retrieval configuration
        """
        self.vectordb = vectordb
        self.embedder = embedder
        self.config = config

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult, sorted by relevance
        """
        # 1. Preprocess query if enabled
        if self.config.query_preprocessing:
            query = self._preprocess_query(query)

        # 2. Embed query
        query_embedding = await self.embedder.embed_query(query)

        # 3. Determine search size (fetch more if MMR enabled)
        fetch_k = top_k * 2 if self.config.mmr_enabled else top_k

        # 4. Vector search
        results = await self.vectordb.search(
            query_embedding=query_embedding,
            top_k=fetch_k,
            filters=filters,
        )

        # Convert to SearchResult
        search_results = [
            SearchResult(chunk=chunk, score=score, metadata=chunk.metadata)
            for chunk, score in results
        ]

        # 5. Apply MMR if enabled
        if self.config.mmr_enabled and len(search_results) > 0:
            # Get embeddings for results (would need to be stored or re-computed)
            # For now, we'll fetch from the embedder cache or re-compute
            result_texts = [r.chunk.content for r in search_results]
            result_embeddings = await self.embedder.embed_batch(result_texts)

            search_results = maximal_marginal_relevance(
                query_embedding=query_embedding,
                results=search_results,
                embeddings=[result_embeddings[i] for i in range(len(search_results))],
                lambda_param=self.config.mmr_lambda,
                top_k=top_k,
                diversity_threshold=self.config.diversity_threshold,
            )
        else:
            # Just take top_k
            search_results = search_results[:top_k]

        # 6. Filter by score threshold
        if self.config.score_threshold > 0:
            search_results = [r for r in search_results if r.score >= self.config.score_threshold]

        return search_results

    def index_documents(self, chunks: list[Chunk]) -> None:
        """Index documents for semantic search.

        Note: For semantic retrieval, documents are typically indexed directly
        into the VectorDB during the ingestion pipeline. This method is here
        for interface compatibility but may not be used in practice.

        Args:
            chunks: List of chunks to index
        """
        # This would typically be done during ingestion
        # The VectorDB is already populated
        pass

    def _preprocess_query(self, query: str) -> str:
        """Preprocess query text.

        Args:
            query: Raw query

        Returns:
            Preprocessed query
        """
        # Strip whitespace
        query = query.strip()

        # Normalize whitespace
        query = " ".join(query.split())

        return query
