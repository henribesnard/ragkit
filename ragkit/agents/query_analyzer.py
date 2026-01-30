"""Query analyzer agent."""

from __future__ import annotations

from ragkit.config.schema import QueryAnalyzerConfig
from ragkit.llm.litellm_provider import LLMProvider
from ragkit.models import QueryAnalysis


class QueryAnalyzerAgent:
    """Analyze user queries to decide whether retrieval is needed."""

    def __init__(self, config: QueryAnalyzerConfig, llm: LLMProvider):
        self.config = config
        self.llm = llm
        self.system_prompt = config.system_prompt
        self.output_schema = config.output_schema

    async def analyze(self, query: str, history: list[dict] | None = None) -> QueryAnalysis:
        if self.config.behavior.always_retrieve:
            return QueryAnalysis(
                intent="question",
                needs_retrieval=True,
                rewritten_query=query,
                reasoning="Always retrieve mode enabled",
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analyze this query: {query}"},
        ]

        result = await self.llm.complete_json(messages, self.output_schema)
        analysis = QueryAnalysis(**result)

        if analysis.needs_retrieval and self.config.behavior.query_rewriting.enabled:
            if not analysis.rewritten_query:
                analysis.rewritten_query = query

        return analysis
