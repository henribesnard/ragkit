"""Response generator agent."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from ragkit.config.schema import ResponseGeneratorConfig
from ragkit.llm.litellm_provider import LLMProvider
from ragkit.models import GeneratedResponse, QueryAnalysis, RetrievalResult
from ragkit.utils.language import detect_language, language_name


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
            return GeneratedResponse(
                content=response, sources=[], metadata={"intent": analysis.intent}
            )

        if analysis.intent == "out_of_scope":
            prompt = self._build_out_of_scope_prompt(query, history)
            response = await self.llm.complete(prompt)
            return GeneratedResponse(
                content=response, sources=[], metadata={"intent": analysis.intent}
            )

        prompt = self._build_rag_prompt(query, context or [], history)
        response = await self.llm.complete(prompt)
        sources = self._extract_sources(context or [])
        return GeneratedResponse(
            content=response, sources=sources, metadata={"intent": analysis.intent}
        )

    async def generate_stream(
        self,
        query: str,
        context: list[RetrievalResult] | None,
        analysis: QueryAnalysis,
        history: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        if not analysis.needs_retrieval:
            prompt = self._build_no_retrieval_prompt(query, history)
            async for token in self.llm.complete_stream(prompt):
                yield token
            return

        if analysis.intent == "out_of_scope":
            prompt = self._build_out_of_scope_prompt(query, history)
            async for token in self.llm.complete_stream(prompt):
                yield token
            return

        prompt = self._build_rag_prompt(query, context or [], history)
        async for token in self.llm.complete_stream(prompt):
            yield token

    def extract_sources(self, context: list[RetrievalResult] | None) -> list[str]:
        return self._extract_sources(context or [])

    def _build_rag_prompt(
        self,
        query: str,
        context: list[RetrievalResult],
        history: list[dict] | None = None,
    ) -> list[dict[str, str]]:
        formatted_context = self._format_context(context)
        system = self.config.system_prompt.format(context=formatted_context)
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        language_instruction = self._language_instruction(query)
        if language_instruction:
            messages.append({"role": "system", "content": language_instruction})
        messages.extend(self._history_messages(history))
        messages.append({"role": "user", "content": query})
        return messages

    def _build_no_retrieval_prompt(
        self, query: str, history: list[dict] | None = None
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.config.no_retrieval_prompt}
        ]
        language_instruction = self._language_instruction(query)
        if language_instruction:
            messages.append({"role": "system", "content": language_instruction})
        messages.extend(self._history_messages(history))
        messages.append({"role": "user", "content": query})
        return messages

    def _build_out_of_scope_prompt(
        self, query: str, history: list[dict] | None = None
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.config.out_of_scope_prompt}
        ]
        language_instruction = self._language_instruction(query)
        if language_instruction:
            messages.append({"role": "system", "content": language_instruction})
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
            source = _source_name(result, self.config.behavior.source_path_mode)
            snippet = result.chunk.content.strip().replace("\n", " ")
            lines.append(f"[{idx}] {source}: {snippet}")
        return "\n".join(lines)

    def _extract_sources(self, context: Iterable[RetrievalResult]) -> list[str]:
        seen: set[str] = set()
        sources: list[str] = []
        for result in context:
            source = _source_name(result, self.config.behavior.source_path_mode)
            if source not in seen:
                seen.add(source)
                sources.append(source)
        return sources

    def _language_instruction(self, query: str) -> str | None:
        preference = (self.config.behavior.response_language or "").strip()
        if not preference:
            return None
        normalized = preference.lower()
        if normalized in {"auto", "match_query"}:
            detected = detect_language(query)
            if not detected:
                return None
            return f"Respond in {language_name(detected)}."
        if normalized == "match_documents":
            return None
        return f"Respond in {language_name(preference)}."


def _source_name(result: RetrievalResult, mode: str = "basename") -> str:
    metadata = result.chunk.metadata
    source = (
        metadata.get("source")
        or metadata.get("source_path")
        or metadata.get("file_name")
        or result.chunk.document_id
    )
    return _sanitize_source(source, mode)


def _sanitize_source(source: str, mode: str) -> str:
    if source is None:
        return ""
    if mode == "full":
        return source
    if mode == "basename":
        normalized = source.replace("\\", "/")
        return normalized.rsplit("/", maxsplit=1)[-1]
    return source
