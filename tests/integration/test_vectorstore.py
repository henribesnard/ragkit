import pytest

from ragkit.config.schema import ChromaConfig, QdrantConfig
from ragkit.models import Chunk
from ragkit.vectorstore.providers.chroma import ChromaVectorStore
from ragkit.vectorstore.providers.qdrant import QdrantVectorStore


@pytest.mark.asyncio
async def test_qdrant_add_and_search():
    pytest.importorskip("qdrant_client")
    config = QdrantConfig(mode="memory", collection_name="test_qdrant")
    store = QdrantVectorStore(config)

    chunks = [
        Chunk(
            id="1",
            document_id="doc1",
            content="Doc A",
            metadata={"category": "tech"},
            embedding=[0.1, 0.2, 0.3],
        ),
        Chunk(
            id="2",
            document_id="doc2",
            content="Doc B",
            metadata={"category": "finance"},
            embedding=[0.0, 0.1, 0.2],
        ),
    ]

    await store.add(chunks)
    results = await store.search([0.1, 0.2, 0.3], top_k=2)
    assert results
    await store.clear()


@pytest.mark.asyncio
async def test_chroma_add_and_search():
    pytest.importorskip("chromadb")
    config = ChromaConfig(mode="memory", collection_name="test_chroma")
    store = ChromaVectorStore(config)

    chunks = [
        Chunk(
            id="1",
            document_id="doc1",
            content="Doc A",
            metadata={"category": "tech"},
            embedding=[0.1, 0.2, 0.3],
        )
    ]

    await store.add(chunks)
    results = await store.search([0.1, 0.2, 0.3], top_k=1)
    assert results
    await store.clear()
