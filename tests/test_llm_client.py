"""Tests for LLMClient behavior."""

import pytest

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.llm_client import LLMClient


@pytest.mark.asyncio
async def test_llm_client_caching(monkeypatch):
    config = LLMGenerationConfigV2(cache_responses=True, cache_ttl=3600, max_retries=0)
    client = LLMClient(config)
    calls: list[str] = []

    async def fake_call(prompt: str, system_prompt: str | None):
        calls.append(prompt)
        return "ok"

    monkeypatch.setattr(client, "_call_provider", fake_call)
    first = await client.generate("hello")
    second = await client.generate("hello")

    assert first == "ok"
    assert second == "ok"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_llm_client_retry(monkeypatch):
    config = LLMGenerationConfigV2(max_retries=2, retry_delay=0)
    client = LLMClient(config)
    attempts = {"count": 0}

    async def flaky_call(prompt: str, system_prompt: str | None):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("boom")
        return "ok"

    monkeypatch.setattr(client, "_call_provider", flaky_call)
    result = await client.generate("retry")
    assert result == "ok"
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_llm_client_generate_stream(monkeypatch):
    config = LLMGenerationConfigV2(stream=False)
    client = LLMClient(config)

    async def fake_call(prompt: str, system_prompt: str | None):
        return "streamed"

    monkeypatch.setattr(client, "_call_provider", fake_call)
    chunks = [chunk async for chunk in client.generate_stream("hi")]
    assert chunks == ["streamed"]
