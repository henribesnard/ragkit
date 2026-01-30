"""Qdrant vector store implementation."""

from __future__ import annotations

from typing import Any

import uuid

from ragkit.config.schema import QdrantConfig
from ragkit.exceptions import RetrievalError
from ragkit.models import Chunk
from ragkit.vectorstore.base import BaseVectorStore, SearchResult


def _distance(metric: str):
    from qdrant_client.models import Distance

    return {
        "cosine": Distance.COSINE,
        "euclidean": Distance.EUCLID,
        "dot": Distance.DOT,
    }[metric]


class QdrantVectorStore(BaseVectorStore):
    def __init__(self, config: QdrantConfig):
        try:
            from qdrant_client import QdrantClient
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError("qdrant-client is required") from exc

        self.config = config
        if config.mode == "memory":
            self.client = QdrantClient(location=":memory:")
        elif config.mode == "local":
            self.client = QdrantClient(path=config.path)
        else:
            self.client = QdrantClient(url=config.url, api_key=config.api_key)
        self.collection_name = config.collection_name
        self._vector_size: int | None = None

    async def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        if any(chunk.embedding is None for chunk in chunks):
            raise RetrievalError("All chunks must have embeddings before adding")

        if self._vector_size is None:
            self._vector_size = len(chunks[0].embedding or [])
        await self._ensure_collection(self._vector_size)

        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=_normalize_id(chunk.id),
                vector=chunk.embedding,
                payload={
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "document_id": chunk.document_id,
                    "original_id": chunk.id,
                },
            )
            for chunk in chunks
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        qdrant_filter = _build_filter(filters)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
        )

        matches: list[SearchResult] = []
        for result in results:
            payload = result.payload or {}
            metadata = payload.get("metadata", {})
            payload_id = payload.get("original_id")
            chunk = Chunk(
                id=str(payload_id or result.id),
                document_id=str(payload.get("document_id", "")),
                content=str(payload.get("content", "")),
                metadata=metadata,
                embedding=None,
            )
            matches.append(SearchResult(chunk=chunk, score=float(result.score)))
        return matches

    async def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        normalized = [_normalize_id(item) for item in ids]
        self.client.delete(collection_name=self.collection_name, points_selector=normalized)

    async def clear(self) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self._vector_size = None

    async def _ensure_collection(self, vector_size: int) -> None:
        if self.client.collection_exists(self.collection_name):
            return
        from qdrant_client.models import VectorParams

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=_distance(self.config.distance_metric)),
        )


def _build_filter(filters: dict | None):
    if not filters:
        return None
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()]
    return Filter(must=conditions)


def _normalize_id(raw_id: str | int) -> str | int:
    if isinstance(raw_id, int):
        return raw_id
    if isinstance(raw_id, str):
        try:
            int_value = int(raw_id)
        except ValueError:
            int_value = None
        if int_value is not None:
            return int_value
        try:
            return str(uuid.UUID(raw_id))
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, raw_id))
    return str(raw_id)
