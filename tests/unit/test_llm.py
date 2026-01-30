import sys
import types

import pytest

from ragkit.config.schema import LLMConfig, LLMModelConfig, LLMParams
from ragkit.llm.litellm_provider import LLMProvider, LLMRouter

from tests.helpers import DummyChoice, DummyResponse


@pytest.mark.asyncio
async def test_llm_completion(monkeypatch):
    async def fake_completion(**kwargs):
        return DummyResponse("Hello")

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(acompletion=fake_completion))

    config = LLMModelConfig(provider="openai", model="gpt-4o-mini", api_key="test", params=LLMParams())
    llm = LLMProvider(config)

    response = await llm.complete([{"role": "user", "content": "Hello"}])
    assert response == "Hello"


@pytest.mark.asyncio
async def test_llm_json_output(monkeypatch):
    async def fake_completion(**kwargs):
        return DummyResponse("{\"name\": \"Alice\"}")

    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(acompletion=fake_completion))

    config = LLMModelConfig(provider="openai", model="gpt-4o-mini", api_key="test", params=LLMParams())
    llm = LLMProvider(config)

    result = await llm.complete_json(
        [{"role": "user", "content": "Return JSON"}],
        {"type": "object", "properties": {"name": {"type": "string"}}},
    )
    assert result["name"] == "Alice"


def test_llm_router():
    config = LLMConfig(
        primary=LLMModelConfig(provider="openai", model="gpt-4o-mini", api_key="test", params=LLMParams()),
        secondary=None,
        fast=None,
    )
    router = LLMRouter(config)
    assert router.get("primary")
