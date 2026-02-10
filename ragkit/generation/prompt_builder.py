"""Prompt assembly for RAG generation."""

from __future__ import annotations

from ragkit.config.schema_v2 import LLMGenerationConfigV2


class PromptBuilder:
    """Builds prompts for RAG generation."""

    def __init__(self, config: LLMGenerationConfigV2) -> None:
        self.config = config

    def build_rag_prompt(self, query: str, context: str) -> str:
        """Construct a RAG prompt from query and context."""
        prompt_parts: list[str] = []

        if self.config.few_shot_examples:
            prompt_parts.append("Examples:\n")
            for example in self.config.few_shot_examples:
                question = example.get("question", "")
                answer = example.get("answer", "")
                prompt_parts.append(f"Q: {question}\nA: {answer}\n")

        prompt_parts.append(context.strip())
        prompt_parts.append(f"\nQuestion: {query}\n")

        prompt_parts.append("Instructions:")
        prompt_parts.append("- Answer ONLY based on the provided context")

        if self.config.cite_sources:
            if self.config.citation_format == "numbered":
                prompt_parts.append("- Cite your sources using [1], [2], [3]")
            elif self.config.citation_format == "inline":
                prompt_parts.append("- Cite sources inline (Source: filename, p.X)")
            elif self.config.citation_format == "footnote":
                prompt_parts.append("- Cite sources using footnotes (e.g., ¹, ²)")

        if self.config.require_citation_for_facts:
            prompt_parts.append("- Every factual claim MUST have a citation")

        if self.config.enable_fallback:
            prompt_parts.append(
                f"- If context is insufficient, say '{self.config.fallback_message}'"
            )

        if self.config.output_format == "json" and self.config.json_schema:
            prompt_parts.append(
                f"- Return ONLY valid JSON matching this schema:\n{self.config.json_schema}"
            )
        elif self.config.output_format == "markdown":
            prompt_parts.append("- Format the response in Markdown")

        prompt_parts.append("")

        if self.config.chain_of_thought:
            prompt_parts.append("Let's think step by step:\n")

        prompt_parts.append("Answer:\n")

        return "\n".join(prompt_parts).strip() + "\n"
