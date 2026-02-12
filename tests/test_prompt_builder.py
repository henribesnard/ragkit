"""Tests for prompt builder output."""

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.prompt_builder import PromptBuilder


def test_prompt_builder_includes_examples_and_citations():
    config = LLMGenerationConfigV2(
        cite_sources=True,
        citation_format="numbered",
        few_shot_examples=[
            {"question": "What is RAG?", "answer": "Retrieval augmented generation."}
        ],
        enable_fallback=True,
        chain_of_thought=True,
    )
    builder = PromptBuilder(config)
    context = "[1] Source: manual\nSome content."
    prompt = builder.build_rag_prompt("Explain RAG", context)

    assert "Examples:" in prompt
    assert "Retrieval augmented generation." in prompt
    assert "Cite your sources using [1]" in prompt
    assert config.fallback_message in prompt
    assert "Let's think step by step" in prompt


def test_prompt_builder_json_output_instruction():
    config = LLMGenerationConfigV2(
        output_format="json",
        json_schema={"type": "object", "properties": {"answer": {"type": "string"}}},
    )
    builder = PromptBuilder(config)
    prompt = builder.build_rag_prompt("Query", "[1] Source: doc\nAnswer in JSON.")
    assert "Return ONLY valid JSON" in prompt
