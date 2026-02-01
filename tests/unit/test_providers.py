import sys
import types

import pytest

from ragkit.config.schema import EmbeddingModelConfig, EmbeddingParams, LLMModelConfig, LLMParams
from ragkit.embedding import create_embedder
from ragkit.embedding.providers.litellm import LiteLLMEmbedder
from ragkit.llm.litellm_provider import _resolve_model_name


def test_resolve_model_name_openai():
    cfg = LLMModelConfig(provider="openai", model="gpt-4o-mini", api_key="test", params=LLMParams())
    assert _resolve_model_name(cfg) == "gpt-4o-mini"


def test_resolve_model_name_deepseek():
    cfg = LLMModelConfig(
        provider="deepseek", model="deepseek-chat", api_key="test", params=LLMParams()
    )
    assert _resolve_model_name(cfg) == "deepseek/deepseek-chat"


def test_resolve_model_name_groq():
    cfg = LLMModelConfig(
        provider="groq", model="llama-3.1-70b-versatile", api_key="test", params=LLMParams()
    )
    assert _resolve_model_name(cfg) == "groq/llama-3.1-70b-versatile"


def test_resolve_model_name_mistral():
    cfg = LLMModelConfig(
        provider="mistral", model="mistral-large-latest", api_key="test", params=LLMParams()
    )
    assert _resolve_model_name(cfg) == "mistral/mistral-large-latest"


def test_resolve_model_name_ollama():
    cfg = LLMModelConfig(provider="ollama", model="llama3", params=LLMParams())
    assert _resolve_model_name(cfg) == "ollama/llama3"


def test_resolve_model_name_with_slash():
    cfg = LLMModelConfig(provider="ollama", model="ollama/llama3", params=LLMParams())
    assert _resolve_model_name(cfg) == "ollama/llama3"


def test_litellm_embedder_creation():
    cfg = EmbeddingModelConfig(
        provider="litellm",
        model="mistral/mistral-embed",
        api_key="test",
        params=EmbeddingParams(dimensions=1024),
    )
    embedder = create_embedder(cfg)
    assert isinstance(embedder, LiteLLMEmbedder)
    assert embedder.dimensions == 1024


@pytest.mark.asyncio
async def test_litellm_embedder_embed(monkeypatch):
    async def fake_embedding(**_kwargs):
        return types.SimpleNamespace(data=[{"embedding": [0.1, 0.2, 0.3]}])

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(aembedding=fake_embedding))

    cfg = EmbeddingModelConfig(
        provider="litellm",
        model="mistral/mistral-embed",
        api_key="test",
        params=EmbeddingParams(dimensions=3),
    )
    embedder = LiteLLMEmbedder(cfg)
    result = await embedder.embed(["hello"])
    assert result == [[0.1, 0.2, 0.3]]
