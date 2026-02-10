"""ChromaDB adapter for vector database with VectorDBConfigV2 support."""

from __future__ import annotations

import chromadb
import numpy as np
from chromadb.config import Settings

from ragkit.config.schema_v2 import VectorDBConfigV2
from ragkit.models import Chunk


class ChromaDBAdapter:
    """Adapter for ChromaDB.

    ChromaDB is a local, open-source vector database, easy to use.
    Ideal for prototyping and datasets <1M vectors.
    """

    def __init__(self, config: VectorDBConfigV2):
        """Initialize the ChromaDB adapter.

        Args:
            config: Vector DB configuration
        """
        self.config = config

        # ChromaDB client
        if config.in_memory:
            self.client = chromadb.Client()
        else:
            storage_path = config.storage_path or "./data/vectordb"
            self.client = chromadb.PersistentClient(
                path=storage_path,
                settings=Settings(
                    anonymized_telemetry=False,
                ),
            )

        # Collection
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Retrieve or create the ChromaDB collection.

        Returns:
            ChromaDB collection
        """
        # Convert distance_metric to ChromaDB format
        distance_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot_product": "ip",  # inner product
        }

        distance = distance_map.get(self.config.distance_metric, "cosine")

        # HNSW config
        metadata = {
            "hnsw:space": distance,
            "hnsw:construction_ef": self.config.hnsw_ef_construction,
            "hnsw:M": self.config.hnsw_m,
            "hnsw:search_ef": self.config.hnsw_ef_search,
        }

        return self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata=metadata,
        )

    async def insert_batch(
        self,
        chunks: list[Chunk],
        embeddings: np.ndarray,
    ):
        """Insert a batch of chunks with their embeddings.

        Args:
            chunks: List of chunks to insert
            embeddings: Corresponding embeddings (shape: len(chunks) x dims)
        """
        if len(chunks) == 0:
            return

        # Prepare data for ChromaDB
        ids = [self._generate_id(chunk, i) for i, chunk in enumerate(chunks)]
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = dict(chunk.metadata)
            if "document_id" not in metadata:
                metadata["document_id"] = chunk.document_id or chunk.id
            if not metadata:
                metadata = {"document_id": chunk.document_id or chunk.id}
            metadatas.append(metadata)
        embeddings_list = embeddings.tolist()

        # Insert by batch
        batch_size = self.config.batch_size

        for i in range(0, len(chunks), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_documents = documents[i : i + batch_size]
            batch_metadatas = metadatas[i : i + batch_size]
            batch_embeddings = embeddings_list[i : i + batch_size]

            self.collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings,
            )

    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Search for the top_k most similar vectors.

        Args:
            query_embedding: Query vector (shape: dims)
            top_k: Number of results to return
            filters: Filters on metadata (ex: {"source": "manual.pdf"})

        Returns:
            List of tuples (Chunk, score)
        """
        # Convert filters to ChromaDB format
        where = self._convert_filters(filters) if filters else None

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where,
        )

        # Convert results to Chunk
        chunks_with_scores = []

        if results["ids"]:
            for i in range(len(results["ids"][0])):
                chunk = Chunk(
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                )

                # Score (distance or similarity depending on metric)
                raw_distance = results["distances"][0][i] if "distances" in results else None
                score = (
                    self._convert_distance_to_score(raw_distance)
                    if raw_distance is not None
                    else 1.0
                )

                chunks_with_scores.append((chunk, score))

        chunks_with_scores.sort(key=lambda item: item[1], reverse=True)
        return chunks_with_scores

    def _generate_id(self, chunk: Chunk, index: int) -> str:
        """Generate a unique ID for a chunk.

        Args:
            chunk: Chunk
            index: Index of chunk in batch

        Returns:
            Unique ID
        """
        # Use metadata.chunk_id if available
        if "chunk_id" in chunk.metadata:
            return chunk.metadata["chunk_id"]

        # Otherwise, generate an ID based on content
        import hashlib

        content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:8]
        return f"chunk_{index}_{content_hash}"

    def _convert_filters(self, filters: dict) -> dict:
        """Convert filters to ChromaDB format.

        Args:
            filters: Standard filters

        Returns:
            ChromaDB format filters
        """
        # ChromaDB where clause: {"field": "value"} or {"$and": [...]}
        # For now, simple equality
        return filters

    def _convert_distance_to_score(self, distance: float) -> float:
        """Convert a distance value to a similarity score (higher is better)."""
        metric = self.config.distance_metric
        if metric == "cosine":
            return 1.0 - float(distance)
        if metric in {"euclidean", "manhattan"}:
            return -float(distance)
        # For dot_product and others, assume larger is better already.
        return float(distance)
