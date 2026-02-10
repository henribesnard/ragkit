"""Tests for response validator behavior."""

import pytest

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.response_validator import ResponseValidator


@pytest.mark.asyncio
async def test_validator_requires_citations():
    config = LLMGenerationConfigV2(
        cite_sources=True,
        citation_format="numbered",
        confidence_threshold=0.0,
    )
    validator = ResponseValidator(config)
    result = await validator.validate("Answer without citations.", "Context", "Query")
    assert result.valid is False
    assert "No citations found" in result.issues


@pytest.mark.asyncio
async def test_validator_accepts_numbered_citations():
    config = LLMGenerationConfigV2(
        cite_sources=True,
        citation_format="numbered",
        confidence_threshold=0.0,
    )
    validator = ResponseValidator(config)
    response = "Use API keys for auth [1]."
    result = await validator.validate(response, "Context", "Query")
    assert result.valid is True


@pytest.mark.asyncio
async def test_validator_pii_filter_flags_email():
    config = LLMGenerationConfigV2(
        cite_sources=False,
        require_citation_for_facts=False,
        content_filters=["pii"],
        confidence_threshold=0.0,
    )
    validator = ResponseValidator(config)
    response = "Contact me at test@example.com."
    result = await validator.validate(response, "Context", "Query")
    assert result.valid is False
    assert any("pii" in issue for issue in result.issues)


@pytest.mark.asyncio
async def test_validator_faithfulness_threshold(monkeypatch):
    config = LLMGenerationConfigV2(
        cite_sources=False,
        require_citation_for_facts=False,
        content_filters=[],
        confidence_threshold=0.5,
    )
    validator = ResponseValidator(config)

    async def fake_faithfulness(response: str, context: str, query: str) -> float:
        return 0.2

    monkeypatch.setattr(
        "ragkit.generation.response_validator.compute_faithfulness",
        fake_faithfulness,
    )

    result = await validator.validate("Answer", "Context", "Query")
    assert result.valid is False
    assert any("faithfulness" in issue.lower() for issue in result.issues)
