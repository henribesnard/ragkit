"""Agent orchestrator for end-to-end RAG responses."""

from __future__ import annotations

from ragkit.config.schema import AgentsConfig
from ragkit.llm.litellm_provider import LLMRouter
from ragkit.models import GeneratedResponse, QueryAnalysis, RAGResponse, RetrievalResult
from ragkit.retrieval.engine import RetrievalEngine
from ragkit.agents.query_analyzer import QueryAnalyzerAgent
from ragkit.agents.response_generator import ResponseGeneratorAgent


class AgentOrchestrator:
    """Orchestrate query analysis, retrieval, and response generation."""

    def __init__(
        self,
        config: AgentsConfig,
        retrieval_engine: RetrievalEngine,
        llm_router: LLMRouter,
    ) -> None:
        self.query_analyzer = QueryAnalyzerAgent(
            config.query_analyzer,
            llm_router.get(config.query_analyzer.llm),
        )
        self.response_generator = ResponseGeneratorAgent(
            config.response_generator,
            llm_router.get(config.response_generator.llm),
        )
        self.retrieval = retrieval_engine

    async def process(self, query: str, history: list[dict] | None = None) -> RAGResponse:
        analysis = await self.query_analyzer.analyze(query, history)

        context: list[RetrievalResult] | None = None
        if analysis.needs_retrieval:
            search_query = analysis.rewritten_query or query
            context = await self.retrieval.retrieve(search_query)

        response = await self.response_generator.generate(query, context, analysis, history)

        return RAGResponse(query=query, analysis=analysis, context=context, response=response)
