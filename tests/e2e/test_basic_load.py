import math

import pytest

from ragkit.config.schema import (
    ChunkingConfig,
    FixedChunkingConfig,
    IngestionConfig,
    LexicalPreprocessingConfig,
    LexicalRetrievalConfig,
    MetadataConfig,
    ParsingConfig,
    RetrievalConfig,
    SemanticRetrievalConfig,
    SourceConfig,
)
from ragkit.embedding.base import BaseEmbedder
from ragkit.ingestion import IngestionPipeline
from ragkit.models import Chunk
from ragkit.retrieval.engine import RetrievalEngine
from ragkit.vectorstore.base import BaseVectorStore, SearchResult


class DummyEmbedder(BaseEmbedder):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._to_vec(text) for text in texts]

    async def embed_query(self, query: str) -> list[float]:
        return self._to_vec(query)

    def _to_vec(self, text: str) -> list[float]:
        length = float(len(text)) or 1.0
        return [length, length / 2.0, 1.0]

    @property
    def dimensions(self) -> int | None:
        return 3


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self._chunks: list[Chunk] = []

    async def add(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)

    async def search(self, query_embedding: list[float], top_k: int, filters: dict | None = None):
        scored = []
        for chunk in self._chunks:
            if chunk.embedding is None:
                continue
            score = _cosine(chunk.embedding, query_embedding)
            scored.append(SearchResult(chunk=chunk, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    async def delete(self, ids: list[str]) -> None:
        self._chunks = [chunk for chunk in self._chunks if chunk.id not in ids]

    async def clear(self) -> None:
        self._chunks = []

    async def count(self) -> int:
        return len(self._chunks)

    async def stats(self):
        from ragkit.vectorstore.base import VectorStoreStats

        return VectorStoreStats(
            provider="memory", collection_name="memory", vector_count=len(self._chunks)
        )

    async def list_documents(self) -> list[str]:
        return sorted({chunk.document_id for chunk in self._chunks})

    async def list_chunks(self) -> list[Chunk]:
        return list(self._chunks)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_basic_load(sample_docs):
    ingestion_config = IngestionConfig(
        sources=[
            SourceConfig(
                type="local", path=str(sample_docs), patterns=["*.md", "*.txt"], recursive=True
            )
        ],
        parsing=ParsingConfig(),
        chunking=ChunkingConfig(
            strategy="fixed", fixed=FixedChunkingConfig(chunk_size=50, chunk_overlap=10)
        ),
        metadata=MetadataConfig(extract=["source_path"], custom={}),
    )

    embedder = DummyEmbedder()
    vector_store = InMemoryVectorStore()
    pipeline = IngestionPipeline(ingestion_config, embedder=embedder, vector_store=vector_store)
    await pipeline.run()

    retrieval_config = RetrievalConfig(
        architecture="semantic",
        semantic=SemanticRetrievalConfig(
            enabled=True, top_k=5, similarity_threshold=0.0, weight=1.0
        ),
        lexical=LexicalRetrievalConfig(
            enabled=False,
            top_k=5,
            preprocessing=LexicalPreprocessingConfig(lowercase=True, remove_stopwords=True),
        ),
    )

    engine = RetrievalEngine(retrieval_config, vector_store, embedder)

    for _ in range(20):
        results = await engine.retrieve("capital of France")
        assert results


def _cosine(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
