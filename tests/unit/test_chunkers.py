from ragkit.config.schema import SemanticChunkingConfig
from ragkit.ingestion.chunkers.fixed import FixedChunker
from ragkit.ingestion.chunkers.semantic import SemanticChunker
from ragkit.ingestion.parsers.base import ParsedDocument


def test_fixed_chunker_produces_chunks():
    doc = ParsedDocument(
        content="This is a test document with several words to chunk.",
        metadata={"document_id": "doc1"},
    )
    chunker = FixedChunker(chunk_size=5, chunk_overlap=2)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    assert chunks[0].metadata["chunk_index"] == 0


def test_semantic_chunker_fallback():
    doc = ParsedDocument(
        content="Sentence one. Sentence two. Sentence three.",
        metadata={"document_id": "doc2"},
    )
    config = SemanticChunkingConfig(
        similarity_threshold=0.85,
        min_chunk_size=1,
        max_chunk_size=10,
        embedding_model="document_model",
    )
    chunker = SemanticChunker(config, embedder=None)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 1
