"""Vector store factory and exports."""

from __future__ import annotations

from ragkit.config.schema import VectorStoreConfig
from ragkit.vectorstore.base import BaseVectorStore
from ragkit.vectorstore.providers.chroma import ChromaVectorStore
from ragkit.vectorstore.providers.qdrant import QdrantVectorStore


def create_vector_store(config: VectorStoreConfig) -> BaseVectorStore:
    if config.provider == "qdrant":
        return QdrantVectorStore(config.qdrant)
    if config.provider == "chroma":
        return ChromaVectorStore(config.chroma)
    raise ValueError(f"Unknown vector store provider: {config.provider}")


__all__ = ["BaseVectorStore", "QdrantVectorStore", "ChromaVectorStore", "create_vector_store"]
