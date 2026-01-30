import pytest

from ragkit.agents.orchestrator import AgentOrchestrator
from ragkit.agents.query_analyzer import QueryAnalyzerAgent
from ragkit.agents.response_generator import ResponseGeneratorAgent
from ragkit.config.schema import (
    AgentsConfig,
    AgentsGlobalConfig,
    QueryAnalyzerBehaviorConfig,
    QueryAnalyzerConfig,
    QueryRewritingConfig,
    ResponseBehaviorConfig,
    ResponseGeneratorConfig,
)
from ragkit.models import Chunk, QueryAnalysis, RetrievalResult
from tests.helpers import DummyLLM, DummyRetrieval, DummyRouter


@pytest.mark.asyncio
async def test_query_analyzer_greeting():
    llm = DummyLLM(
        json_response={
            "intent": "greeting",
            "needs_retrieval": False,
            "rewritten_query": None,
            "reasoning": "hi",
        }
    )
    config = QueryAnalyzerConfig(
        llm="fast",
        behavior=QueryAnalyzerBehaviorConfig(
            always_retrieve=False,
            detect_intents=["greeting"],
            query_rewriting=QueryRewritingConfig(enabled=True, num_rewrites=1),
        ),
        system_prompt="prompt",
        output_schema={},
    )
    agent = QueryAnalyzerAgent(config, llm)
    result = await agent.analyze("Bonjour")

    assert result.intent == "greeting"
    assert result.needs_retrieval is False


@pytest.mark.asyncio
async def test_query_analyzer_always_retrieve():
    llm = DummyLLM()
    config = QueryAnalyzerConfig(
        llm="fast",
        behavior=QueryAnalyzerBehaviorConfig(
            always_retrieve=True,
            detect_intents=["question"],
            query_rewriting=QueryRewritingConfig(enabled=True, num_rewrites=1),
        ),
        system_prompt="prompt",
        output_schema={},
    )
    agent = QueryAnalyzerAgent(config, llm)
    result = await agent.analyze("Hello")

    assert result.needs_retrieval is True
    assert result.rewritten_query == "Hello"


@pytest.mark.asyncio
async def test_response_generator_with_context():
    llm = DummyLLM(text_response="Paris")
    config = ResponseGeneratorConfig(
        llm="primary",
        behavior=ResponseBehaviorConfig(),
        system_prompt="Context:\n{context}",
        no_retrieval_prompt="Hi",
        out_of_scope_prompt="Out",
    )
    agent = ResponseGeneratorAgent(config, llm)

    analysis = QueryAnalysis(intent="question", needs_retrieval=True)
    chunk = Chunk(
        id="1", document_id="doc1", content="Paris is capital", metadata={"source": "geo.pdf"}
    )
    context = [RetrievalResult(chunk=chunk, score=0.9, retrieval_type="semantic")]

    result = await agent.generate("What is capital?", context, analysis)

    assert "Paris" in result.content
    assert result.sources == ["geo.pdf"]


@pytest.mark.asyncio
async def test_agent_orchestrator_flow():
    llm = DummyLLM(
        json_response={
            "intent": "question",
            "needs_retrieval": True,
            "rewritten_query": "capital france",
            "reasoning": "test",
        },
        text_response="Paris",
    )

    config = AgentsConfig(
        mode="default",
        query_analyzer=QueryAnalyzerConfig(
            llm="fast",
            behavior=QueryAnalyzerBehaviorConfig(
                always_retrieve=False,
                detect_intents=["question"],
                query_rewriting=QueryRewritingConfig(enabled=True, num_rewrites=1),
            ),
            system_prompt="prompt",
            output_schema={},
        ),
        response_generator=ResponseGeneratorConfig(
            llm="primary",
            behavior=ResponseBehaviorConfig(),
            system_prompt="Context:\n{context}",
            no_retrieval_prompt="Hi",
            out_of_scope_prompt="Out",
        ),
        global_config=AgentsGlobalConfig(),
    )

    orchestrator = AgentOrchestrator(config, DummyRetrieval(), DummyRouter(llm))
    result = await orchestrator.process("What is capital?")

    assert result.response.content == "Paris"
    assert result.context is not None
