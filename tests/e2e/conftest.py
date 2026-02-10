"""Pytest fixtures and configuration for E2E tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ragkit.config.schema_v2 import (
    EmbeddingConfigV2,
    RerankingConfigV2,
    RetrievalConfigV2,
    VectorDBConfigV2,
)
from ragkit.embedding.advanced_embedder import AdvancedEmbedder
from ragkit.models import Chunk, Document
from ragkit.reranking.cross_encoder_reranker import CrossEncoderReranker
from ragkit.retrieval.hybrid_retriever import HybridRetriever
from ragkit.retrieval.lexical_retriever import LexicalRetriever
from ragkit.retrieval.semantic_retriever import SemanticRetriever
from ragkit.vectorstore.chromadb_adapter import ChromaDBAdapter


# E2E fixtures are also inherited from tests/conftest.py (sample_docs, etc.)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def benchmark_output_dir() -> Path:
    """Get benchmark output directory."""
    output_dir = Path(__file__).parent / "benchmarks"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def test_documents() -> list[Document]:
    """Create test documents for E2E tests."""
    return [
        Document(
            id="doc_1",
            content="""# API Security Best Practices

Authentication is crucial for API security. Use OAuth 2.0 or JWT tokens
for secure authentication. Always validate tokens and implement rate limiting.

Key points:
- Use HTTPS for all API endpoints
- Implement proper authentication (OAuth 2.0, JWT)
- Add rate limiting to prevent abuse
- Validate all input parameters
- Use API keys for service-to-service communication""",
            metadata={"source": "api_security_guide.md", "category": "security"},
        ),
        Document(
            id="doc_2",
            content="""# Database Optimization Techniques

Database performance is critical for application speed. Use indexing strategically,
optimize queries, and implement caching where appropriate.

Best practices:
- Create indexes on frequently queried columns
- Use EXPLAIN to analyze query performance
- Implement connection pooling
- Cache frequently accessed data
- Use database sharding for horizontal scaling""",
            metadata={"source": "database_optimization.md", "category": "performance"},
        ),
        Document(
            id="doc_3",
            content="""# Machine Learning Fundamentals

Machine learning enables computers to learn from data. Supervised learning
uses labeled data, unsupervised learning finds patterns in unlabeled data.

Key concepts:
- Training data and test data split
- Model evaluation metrics (accuracy, precision, recall)
- Overfitting and underfitting
- Feature engineering
- Cross-validation""",
            metadata={"source": "ml_fundamentals.md", "category": "ml"},
        ),
        Document(
            id="doc_4",
            content="""# Docker Containerization Guide

Docker containers package applications with their dependencies. Use multi-stage
builds to optimize image size. Implement health checks and resource limits.

Commands:
- docker build -t myapp .
- docker run -p 8080:80 myapp
- docker-compose up
- docker logs container_name

Best practices:
- Use .dockerignore to exclude unnecessary files
- Implement multi-stage builds
- Set resource limits (CPU, memory)
- Use official base images""",
            metadata={"source": "docker_guide.md", "category": "devops"},
        ),
        Document(
            id="doc_5",
            content="""# REST API Design Patterns

RESTful APIs use HTTP methods (GET, POST, PUT, DELETE) to perform CRUD operations.
Use proper status codes and implement versioning.

Design principles:
- Use nouns for resource names (e.g., /users, /products)
- HTTP methods: GET (read), POST (create), PUT (update), DELETE (delete)
- Return appropriate status codes (200, 201, 404, 500)
- Implement API versioning (v1, v2)
- Use pagination for large result sets""",
            metadata={"source": "api_design.md", "category": "api"},
        ),
    ]


@pytest.fixture
def test_chunks(test_documents) -> list[Chunk]:
    """Create test chunks from documents."""
    chunks = []
    for doc in test_documents:
        # Split document into smaller chunks
        lines = doc.content.split("\n\n")
        for i, content in enumerate(lines):
            if content.strip():
                chunks.append(
                    Chunk(
                        id=f"{doc.id}_chunk_{i}",
                        content=content.strip(),
                        metadata={
                            **doc.metadata,
                            "parent_id": doc.id,
                            "chunk_index": i,
                        },
                    )
                )
    return chunks


@pytest.fixture
async def rag_pipeline_components():
    """Create RAG pipeline components for testing."""
    # Configs
    embedding_config = EmbeddingConfigV2(
        provider="sentence_transformers",
        model="all-MiniLM-L6-v2",
        cache_embeddings=False,
    )

    vectordb_config = VectorDBConfigV2(
        provider="chromadb",
        in_memory=True,
        collection_name="e2e_test_collection",
    )

    retrieval_config = RetrievalConfigV2(
        retrieval_mode="hybrid",
        alpha=0.5,
        fusion_method="rrf",
        top_k=10,
    )

    reranking_config = RerankingConfigV2(
        reranker_enabled=True,
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        rerank_top_n=10,
        final_top_k=5,
        use_gpu=False,
    )

    # Components
    embedder = AdvancedEmbedder(embedding_config)
    vectordb = ChromaDBAdapter(vectordb_config)

    semantic = SemanticRetriever(vectordb, embedder, retrieval_config)
    lexical = LexicalRetriever(retrieval_config)
    hybrid = HybridRetriever(semantic, lexical, retrieval_config)

    reranker = CrossEncoderReranker(reranking_config)

    yield {
        "embedder": embedder,
        "vectordb": vectordb,
        "semantic": semantic,
        "lexical": lexical,
        "hybrid": hybrid,
        "reranker": reranker,
    }

    # Cleanup
    try:
        await vectordb.delete_collection()
    except:
        pass


@pytest.fixture
def sample_queries() -> list[dict[str, Any]]:
    """Sample queries for testing."""
    return [
        {
            "query": "How to authenticate API requests?",
            "expected_docs": ["doc_1", "doc_5"],
            "category": "security",
        },
        {
            "query": "What are database optimization techniques?",
            "expected_docs": ["doc_2"],
            "category": "performance",
        },
        {
            "query": "What is machine learning?",
            "expected_docs": ["doc_3"],
            "category": "ml",
        },
        {
            "query": "How to use Docker containers?",
            "expected_docs": ["doc_4"],
            "category": "devops",
        },
        {
            "query": "REST API design best practices",
            "expected_docs": ["doc_5"],
            "category": "api",
        },
    ]


def save_benchmark_report(report: dict, filename: str, output_dir: Path = None):
    """Save benchmark report to JSON file."""
    if output_dir is None:
        output_dir = Path(__file__).parent / "benchmarks"
    output_dir.mkdir(exist_ok=True)

    report_path = output_dir / filename
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path


def load_baseline(filename: str, output_dir: Path = None) -> dict:
    """Load baseline metrics from JSON file."""
    if output_dir is None:
        output_dir = Path(__file__).parent / "benchmarks"

    baseline_path = output_dir / filename
    if not baseline_path.exists():
        # Return default baseline if file doesn't exist
        return {
            "faithfulness": 0.85,
            "answer_relevancy": 0.80,
            "precision_at_5": 0.70,
        }

    with open(baseline_path, "r") as f:
        return json.load(f)


@pytest.fixture
def quality_baseline() -> dict:
    """Get quality baseline metrics."""
    return load_baseline("quality_baseline.json")
