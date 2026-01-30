"""Response generator agent."""

from __future__ import annotations

from typing import Iterable

from ragkit.config.schema import ResponseGeneratorConfig
from ragkit.llm.litellm_provider import LLMProvider
from ragkit.models import GeneratedResponse, QueryAnalysis, RetrievalResult


class ResponseGeneratorAgent:
    """Generate the final response using context."""

    def __init__(self, config: ResponseGeneratorConfig, llm: LLMProvider):
        self.config = config
        self.llm = llm

    async def generate(
        self,
        query: str,
        context: list[RetrievalResult] | None,
        analysis: QueryAnalysis,
        history: list[dict] | None = None,
    ) -> GeneratedResponse:
        if not analysis.needs_retrieval:
            prompt = self._build_no_retrieval_prompt(query, history)
            response = await self.llm.complete(prompt)
            return GeneratedResponse(content=response, sources=[], metadata={"intent": analysis.intent})

        if analysis.intent == "out_of_scope":
            prompt = self._build_out_of_scope_prompt(query, history)
            response = await self.llm.complete(prompt)
            return GeneratedResponse(content=response, sources=[], metadata={"intent": analysis.intent})

        prompt = self._build_rag_prompt(query, context or [], history)
        response = await self.llm.complete(prompt)
        sources = self._extract_sources(context or [])
        return GeneratedResponse(content=response, sources=sources, metadata={"intent": analysis.intent})

    def _build_rag_prompt(
        self, query: str, context: list[RetrievalResult], history: list[dict] | None = None,
    ) -> list[dict[str, str]]:
        formatted_context = self._format_context(context)
        system = self.config.system_prompt.format(context=formatted_context)
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(self._history_messages(history))
        messages.append({"role": "user", "content": query})
        return messages

    def _build_no_retrieval_prompt(self, query: str, history: list[dict] | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": self.config.no_retrieval_prompt}]
        messages.extend(self._history_messages(history))
        messages.append({"role": "user", "content": query})
        return messages

    def _build_out_of_scope_prompt(self, query: str, history: list[dict] | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": self.config.out_of_scope_prompt}]
        messages.extend(self._history_messages(history))
        messages.append({"role": "user", "content": query})
        return messages

    @staticmethod
    def _history_messages(history: list[dict] | None) -> list[dict[str, str]]:
        if not history:
            return []
        result: list[dict[str, str]] = []
        for msg in history[-6:]:
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                result.append({"role": role, "content": msg.get("content", "")})
        return result

    def _format_context(self, context: Iterable[RetrievalResult]) -> str:
        lines: list[str] = []
        for idx, result in enumerate(context, start=1):
            source = _source_name(result)
            snippet = result.chunk.content.strip().replace("\n", " ")
            lines.append(f"[{idx}] {source}: {snippet}")
        return "\n".join(lines)

    def _extract_sources(self, context: Iterable[RetrievalResult]) -> list[str]:
        seen: set[str] = set()
        sources: list[str] = []
        for result in context:
            source = _source_name(result)
            if source not in seen:
                seen.add(source)
                sources.append(source)
        return sources


def _source_name(result: RetrievalResult) -> str:
    metadata = result.chunk.metadata
    return (
        metadata.get("source")
        or metadata.get("source_path")
        or metadata.get("file_name")
        or result.chunk.document_id
    )
