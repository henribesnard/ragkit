"""Integration-style test for generation pipeline."""

import pytest

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.context_manager import ContextManager, SimpleTokenizer
from ragkit.generation.llm_client import LLMClient
from ragkit.generation.prompt_builder import PromptBuilder
from ragkit.generation.response_validator import ResponseValidator
from ragkit.models import Document


@pytest.mark.asyncio
async def test_generation_pipeline(monkeypatch):
    config = LLMGenerationConfigV2(
        cite_sources=True,
        citation_format="numbered",
        max_context_tokens=200,
    )
    docs = [
        Document(
            id="doc-1",
            content="API authentication requires an API key in the header.",
            metadata={"source": "manual.pdf", "page": 5},
        )
    ]

    context_manager = ContextManager(config, tokenizer=SimpleTokenizer())
    context = context_manager.prepare_context(docs)

    prompt_builder = PromptBuilder(config)
    prompt = prompt_builder.build_rag_prompt("How to authenticate API calls?", context)

    client = LLMClient(config)

    async def fake_call(prompt_text: str, system_prompt: str | None):
        return "Use an API key in the header [1]."

    monkeypatch.setattr(client, "_call_provider", fake_call)
    response = await client.generate(prompt)

    validator = ResponseValidator(config)
    result = await validator.validate(response, context, "How to authenticate API calls?")

    assert result.valid is True
    assert "[1]" in response
