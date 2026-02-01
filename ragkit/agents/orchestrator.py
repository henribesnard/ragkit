"""Agent orchestrator for end-to-end RAG responses."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable
from typing import Any, TypeVar

from ragkit.agents.query_analyzer import QueryAnalyzerAgent
from ragkit.agents.response_generator import ResponseGeneratorAgent
from ragkit.config.schema import AgentsConfig
from ragkit.llm.litellm_provider import LLMRouter
from ragkit.metrics import MetricsCollector
from ragkit.metrics import metrics as default_metrics
from ragkit.models import QueryAnalysis, RAGResponse, RetrievalResult
from ragkit.retrieval.engine import RetrievalEngine

T = TypeVar("T")


class AgentOrchestrator:
    """Orchestrate query analysis, retrieval, and response generation."""

    def __init__(
        self,
        config: AgentsConfig,
        retrieval_engine: RetrievalEngine,
        llm_router: LLMRouter,
        *,
        metrics_enabled: bool = True,
        metrics_collector: MetricsCollector | None = None,
    ) -> None:
        self.query_analyzer = QueryAnalyzerAgent(
            config.query_analyzer,
            llm_router.get(config.query_analyzer.llm),
            verbose=config.global_config.verbose,
        )
        self.response_generator = ResponseGeneratorAgent(
            config.response_generator,
            llm_router.get(config.response_generator.llm),
        )
        self.retrieval = retrieval_engine
        self.metrics_enabled = metrics_enabled
        self.metrics = metrics_collector or default_metrics

    async def process(self, query: str, history: list[dict] | None = None) -> RAGResponse:
        start = time.perf_counter()
        error: str | None = None
        analysis: QueryAnalysis | None = None
        context: list[RetrievalResult] | None = None
        try:
            analysis = await _timed_component(
                self.metrics,
                self.metrics_enabled,
                "query_analyzer",
                self.query_analyzer.analyze(query, history),
            )

            if analysis.needs_retrieval:
                search_query = analysis.rewritten_query or query
                context = await _timed_component(
                    self.metrics,
                    self.metrics_enabled,
                    "retrieval",
                    self.retrieval.retrieve(search_query),
                )

            response = await _timed_component(
                self.metrics,
                self.metrics_enabled,
                "response_generator",
                self.response_generator.generate(query, context, analysis, history),
            )

            return RAGResponse(query=query, analysis=analysis, context=context, response=response)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            raise
        finally:
            if self.metrics_enabled:
                latency_ms = (time.perf_counter() - start) * 1000
                intent = analysis.intent if analysis else None
                self.metrics.record_query(
                    query=query,
                    latency_ms=latency_ms,
                    success=error is None,
                    intent=intent,
                    error=error,
                )

    async def process_stream(
        self, query: str, history: list[dict] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        start = time.perf_counter()
        error: str | None = None
        analysis: QueryAnalysis | None = None
        context: list[RetrievalResult] | None = None
        response_chunks: list[str] = []
        try:
            analysis = await _timed_component(
                self.metrics,
                self.metrics_enabled,
                "query_analyzer",
                self.query_analyzer.analyze(query, history),
            )

            if analysis.needs_retrieval:
                search_query = analysis.rewritten_query or query
                context = await _timed_component(
                    self.metrics,
                    self.metrics_enabled,
                    "retrieval",
                    self.retrieval.retrieve(search_query),
                )

            sources: list[str] = []
            if analysis.needs_retrieval and analysis.intent != "out_of_scope":
                sources = self.response_generator.extract_sources(context)
            metadata = {"intent": analysis.intent}

            generator_start = time.perf_counter()
            generator_error: str | None = None
            try:
                async for token in self.response_generator.generate_stream(
                    query, context, analysis, history
                ):
                    response_chunks.append(token)
                    yield {"type": "delta", "content": token}
            except Exception as exc:  # noqa: BLE001
                generator_error = str(exc)
                raise
            finally:
                if self.metrics_enabled:
                    latency_ms = (time.perf_counter() - generator_start) * 1000
                    self.metrics.record_component_call(
                        "response_generator",
                        latency_ms,
                        generator_error is None,
                        generator_error,
                    )

            response_text = "".join(response_chunks)
            yield {
                "type": "final",
                "content": response_text,
                "sources": sources,
                "metadata": metadata,
            }
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            yield {"type": "error", "message": error}
            return
        finally:
            if self.metrics_enabled:
                latency_ms = (time.perf_counter() - start) * 1000
                intent = analysis.intent if analysis else None
                self.metrics.record_query(
                    query=query,
                    latency_ms=latency_ms,
                    success=error is None,
                    intent=intent,
                    error=error,
                )


async def _timed_component(
    metrics: MetricsCollector,
    enabled: bool,
    name: str,
    coro: Awaitable[T],
) -> T:
    if not enabled:
        return await coro
    start = time.perf_counter()
    error: str | None = None
    try:
        result = await coro
        return result
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.record_component_call(name, latency_ms, error is None, error)
