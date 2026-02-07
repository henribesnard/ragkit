"""Qdrant vector store implementation."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, cast

from ragkit.config.schema import QdrantConfig
from ragkit.exceptions import RetrievalError
from ragkit.models import Chunk
from ragkit.vectorstore.base import BaseVectorStore, SearchResult, VectorStoreStats


def _distance(metric: str) -> Any:
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

    async def _run_sync(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)

    async def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        if any(chunk.embedding is None for chunk in chunks):
            raise RetrievalError("All chunks must have embeddings before adding")

        if self._vector_size is None:
            self._vector_size = len(chunks[0].embedding or [])
        await self._ensure_collection(self._vector_size)

        from qdrant_client.models import PointStruct

        batch_size = self.config.add_batch_size or len(chunks)
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            points = []
            for chunk in batch:
                embedding = chunk.embedding
                if embedding is None:
                    raise RetrievalError("All chunks must have embeddings before adding")
                points.append(
                    PointStruct(
                        id=_normalize_id(chunk.id),
                        vector=embedding,
                        payload={
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "document_id": chunk.document_id,
                            "original_id": chunk.id,
                        },
                    )
                )
            await self._run_sync(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points,
            )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        qdrant_filter = _build_filter(filters)
        if hasattr(self.client, "query_points"):
            response = await self._run_sync(
                self.client.query_points,
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
            points = _extract_points(response)
        elif hasattr(self.client, "search"):
            results = await self._run_sync(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
            points = results
        else:
            raise RetrievalError("Qdrant client does not support search APIs")

        matches: list[SearchResult] = []
        for result in points:
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
        await self._run_sync(
            self.client.delete,
            collection_name=self.collection_name,
            points_selector=cast(list[Any], normalized),
        )

    async def clear(self) -> None:
        exists = await self._run_sync(self.client.collection_exists, self.collection_name)
        if exists:
            await self._run_sync(self.client.delete_collection, self.collection_name)
        self._vector_size = None

    async def count(self) -> int:
        result = await self._run_sync(
            self.client.count,
            collection_name=self.collection_name,
            exact=True,
        )
        count = getattr(result, "count", None)
        return int(count or 0)

    async def stats(self) -> VectorStoreStats:
        count = await self.count()
        details = {
            "mode": self.config.mode,
            "distance_metric": self.config.distance_metric,
        }
        return VectorStoreStats(
            provider="qdrant",
            collection_name=self.collection_name,
            vector_count=count,
            details=details,
        )

    async def list_documents(self) -> list[str]:
        document_ids: set[str] = set()
        next_offset: Any = None
        exists = await self._run_sync(self.client.collection_exists, self.collection_name)
        if not exists:
            return []
        while True:
            response = await self._run_sync(
                self.client.scroll,
                collection_name=self.collection_name,
                limit=256,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = _extract_scroll(response)
            for point in points:
                payload = getattr(point, "payload", None) or {}
                doc_id = payload.get("document_id")
                if doc_id is not None:
                    document_ids.add(str(doc_id))
            if not next_offset:
                break
        return sorted(document_ids)

    async def list_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        next_offset: Any = None
        exists = await self._run_sync(self.client.collection_exists, self.collection_name)
        if not exists:
            return chunks
        while True:
            response = await self._run_sync(
                self.client.scroll,
                collection_name=self.collection_name,
                limit=256,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = _extract_scroll(response)
            for point in points:
                payload = getattr(point, "payload", None) or {}
                metadata = payload.get("metadata", {}) or {}
                chunk_id = payload.get("original_id") or getattr(point, "id", "")
                chunks.append(
                    Chunk(
                        id=str(chunk_id),
                        document_id=str(payload.get("document_id", "")),
                        content=str(payload.get("content", "")),
                        metadata=metadata,
                        embedding=None,
                    )
                )
            if not next_offset:
                break
        return chunks

    async def _ensure_collection(self, vector_size: int) -> None:
        exists = await self._run_sync(self.client.collection_exists, self.collection_name)
        if exists:
            info = await self._run_sync(self.client.get_collection, self.collection_name)
            existing_size = _extract_vector_size(info)
            if existing_size is not None and existing_size != vector_size:
                raise RetrievalError(
                    "Qdrant collection vector size mismatch: "
                    f"expected {vector_size}, got {existing_size}"
                )
            return
        from qdrant_client.models import VectorParams

        await self._run_sync(
            self.client.create_collection,
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size, distance=_distance(self.config.distance_metric)
            ),
        )


def _build_filter(filters: dict[str, Any] | None) -> Any:
    if not filters:
        return None
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()
    ]
    return Filter(must=cast(list[Any], conditions))


def _extract_points(response: Any) -> list[Any]:
    if response is None:
        return []
    points = getattr(response, "points", None)
    if points is not None:
        return list(points)
    result = getattr(response, "result", None)
    if result is not None:
        return list(result)
    if isinstance(response, dict):
        if "points" in response:
            return list(response["points"])
        if "result" in response:
            return list(response["result"])
    if isinstance(response, list):
        return response
    return []


def _extract_scroll(response: Any) -> tuple[list[Any], Any]:
    if isinstance(response, tuple) and len(response) == 2:
        return list(response[0]), response[1]
    points = getattr(response, "points", None)
    next_offset = getattr(response, "next_page_offset", None)
    if points is None:
        points = []
    return list(points), next_offset


def _extract_vector_size(info: Any) -> int | None:
    if info is None:
        return None
    config = getattr(info, "config", None)
    params = getattr(config, "params", None)
    vectors = getattr(params, "vectors", None)
    size = getattr(vectors, "size", None)
    if size is not None:
        return int(size)
    if isinstance(info, dict):
        try:
            return int(
                info.get("config", {})
                .get("params", {})
                .get("vectors", {})
                .get("size")
            )
        except (TypeError, ValueError):
            return None
    return None


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
