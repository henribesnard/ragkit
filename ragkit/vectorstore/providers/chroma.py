"""Chroma vector store implementation."""

from __future__ import annotations

from typing import Any

from ragkit.config.schema import ChromaConfig
from ragkit.exceptions import RetrievalError
from ragkit.models import Chunk
from ragkit.vectorstore.base import BaseVectorStore, SearchResult, VectorStoreStats


class ChromaVectorStore(BaseVectorStore):
    def __init__(self, config: ChromaConfig):
        try:
            import chromadb  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError("chromadb is required") from exc

        self.config = config
        if config.mode == "persistent":
            self.client = chromadb.PersistentClient(path=config.path)
        else:
            self.client = chromadb.Client()
        self.collection_name = config.collection_name
        self.collection = self.client.get_or_create_collection(self.collection_name)

    async def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        if any(chunk.embedding is None for chunk in chunks):
            raise RetrievalError("All chunks must have embeddings before adding")

        self.collection.add(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            metadatas=[_metadata_payload(chunk) for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
        )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,
        )
        return _to_search_results(results)

    async def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        self.collection.delete(ids=ids)

    async def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(self.collection_name)

    async def count(self) -> int:
        return int(self.collection.count())

    async def stats(self) -> VectorStoreStats:
        count = await self.count()
        details = {
            "mode": self.config.mode,
        }
        return VectorStoreStats(
            provider="chroma",
            collection_name=self.collection_name,
            vector_count=count,
            details=details,
        )

    async def list_documents(self) -> list[str]:
        total = await self.count()
        document_ids: set[str] = set()
        offset = 0
        batch_size = 1000
        while offset < total:
            result = self.collection.get(limit=batch_size, offset=offset, include=["metadatas"])
            metadatas = result.get("metadatas", []) if isinstance(result, dict) else []
            if not metadatas:
                break
            for metadata in metadatas:
                if metadata and "document_id" in metadata:
                    document_ids.add(str(metadata["document_id"]))
            offset += len(metadatas)
        return sorted(document_ids)


def _metadata_payload(chunk: Chunk) -> dict[str, Any]:
    payload = dict(chunk.metadata)
    payload["document_id"] = chunk.document_id
    return payload


def _to_search_results(results: dict) -> list[SearchResult]:
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    matches: list[SearchResult] = []
    for idx, chunk_id in enumerate(ids):
        metadata = metadatas[idx] or {}
        chunk = Chunk(
            id=str(chunk_id),
            document_id=str(metadata.get("document_id", "")),
            content=str(documents[idx]) if documents else "",
            metadata={k: v for k, v in metadata.items() if k != "document_id"},
            embedding=None,
        )
        distance = distances[idx] if distances else 0.0
        score = 1.0 - float(distance) if distance is not None else 0.0
        matches.append(SearchResult(chunk=chunk, score=score))
    return matches
