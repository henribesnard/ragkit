from fastapi.testclient import TestClient

from ragkit.api.app import create_app
from ragkit.config.schema import APIConfig, APICorsConfig, APIDocsConfig, APIServerConfig
from ragkit.models import Chunk, GeneratedResponse, QueryAnalysis, RetrievalResult


class DummyOrchestrator:
    async def process(self, query, history=None):
        analysis = QueryAnalysis(intent="question", needs_retrieval=True)
        chunk = Chunk(id="1", document_id="doc", content="Hello", metadata={"source": "doc"})
        context = [RetrievalResult(chunk=chunk, score=0.9, retrieval_type="semantic")]
        response = GeneratedResponse(content="Answer", sources=["doc"], metadata={})
        return type("RAGResponse", (), {"response": response, "analysis": analysis, "context": context})()


class DummyConfig:
    def __init__(self):
        self.api = APIConfig(
            enabled=True,
            server=APIServerConfig(host="0.0.0.0", port=8000),
            cors=APICorsConfig(enabled=True, origins=["*"]),
            docs=APIDocsConfig(enabled=True, path="/docs"),
        )


def _sample_config():
    return DummyConfig()


def test_query_endpoint():
    app = create_app(_sample_config(), DummyOrchestrator())
    client = TestClient(app)

    response = client.post("/api/v1/query", json={"query": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


def test_streaming_disabled():
    app = create_app(_sample_config(), DummyOrchestrator())
    client = TestClient(app)

    response = client.post("/api/v1/query/stream", json={"query": "Hello"})
    assert response.status_code == 404


def test_streaming_enabled():
    config = _sample_config()
    config.api.streaming.enabled = True
    app = create_app(config, DummyOrchestrator())
    client = TestClient(app)

    response = client.post("/api/v1/query/stream", json={"query": "Hello"})
    assert response.status_code == 200
    assert "data:" in response.text


def test_health_endpoint():
    app = create_app(_sample_config(), DummyOrchestrator())
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
