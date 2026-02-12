"""Tests for context manager ordering and truncation."""

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.context_manager import ContextManager, SimpleTokenizer
from ragkit.models import Document


def test_lost_in_middle_ordering_places_best_on_edges():
    docs = [
        Document(id="1", content="Doc A", metadata={}),
        Document(id="2", content="Doc B", metadata={}),
        Document(id="3", content="Doc C", metadata={}),
        Document(id="4", content="Doc D", metadata={}),
        Document(id="5", content="Doc E", metadata={}),
    ]
    config = LLMGenerationConfigV2(context_ordering="lost_in_middle")
    manager = ContextManager(config, tokenizer=SimpleTokenizer())
    ordered = manager._order_documents(manager._normalize_documents(docs))

    assert ordered[0].content == "Doc A"
    assert ordered[-1].content == "Doc B"


def test_context_truncation_respects_token_budget():
    config = LLMGenerationConfigV2(
        max_context_tokens=50,
        context_window_strategy="truncate_middle",
    )
    manager = ContextManager(config, tokenizer=SimpleTokenizer())
    docs = [
        Document(id=str(i), content="word " * 40, metadata={"source": f"doc{i}"}) for i in range(3)
    ]
    context = manager.prepare_context(docs)
    token_count = len(manager.tokenizer.encode(context))
    assert token_count <= 50
