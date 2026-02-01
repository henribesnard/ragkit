"""Query analyzer agent."""

from __future__ import annotations

import structlog

from ragkit.config.schema import QueryAnalyzerConfig
from ragkit.llm.litellm_provider import LLMProvider
from ragkit.models import QueryAnalysis


class QueryAnalyzerAgent:
    """Analyze user queries to decide whether retrieval is needed."""

    def __init__(self, config: QueryAnalyzerConfig, llm: LLMProvider, *, verbose: bool = False):
        self.config = config
        self.llm = llm
        self.system_prompt = config.system_prompt
        self.output_schema = config.output_schema
        self.verbose = verbose
        self.logger = structlog.get_logger()

    async def analyze(self, query: str, history: list[dict] | None = None) -> QueryAnalysis:
        if self.config.behavior.always_retrieve:
            return QueryAnalysis(
                intent="question",
                needs_retrieval=True,
                rewritten_query=query,
                reasoning="Always retrieve mode enabled",
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ]
        if history:
            for msg in history[-6:]:
                role = msg.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": f"Analyze this query: {query}"})

        result = await self.llm.complete_json(messages, self.output_schema)
        analysis = QueryAnalysis(**result)
        analysis = self._clamp_intent(analysis)

        if analysis.needs_retrieval and self.config.behavior.query_rewriting.enabled:
            if not analysis.rewritten_query:
                analysis.rewritten_query = query

        return analysis

    def _clamp_intent(self, analysis: QueryAnalysis) -> QueryAnalysis:
        allowed = self.config.behavior.detect_intents
        if not allowed:
            return analysis
        if analysis.intent in allowed:
            return analysis

        original_intent = analysis.intent or ""
        lowered = original_intent.lower()
        if "greet" in lowered:
            fallback_intent = "greeting"
            needs_retrieval = False
        else:
            fallback_intent = "question"
            needs_retrieval = True

        if self.verbose:
            self.logger.warning(
                "query_intent_fallback",
                original_intent=original_intent,
                fallback_intent=fallback_intent,
            )

        analysis.intent = fallback_intent
        analysis.needs_retrieval = needs_retrieval
        return analysis
