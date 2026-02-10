"""Tests for retrieval and generation metrics."""

import pytest

from ragkit.config.schema_v2 import MonitoringConfigV2
from ragkit.evaluation.evaluator import RAGEvaluator
from ragkit.models import Document


@pytest.mark.asyncio
async def test_retrieval_metrics_precision_recall_mrr_ndcg():
    config = MonitoringConfigV2(
        precision_at_k=[1, 3],
        recall_at_k=[3],
        track_mrr=True,
        track_ndcg=True,
    )
    evaluator = RAGEvaluator(config)
    retrieved = [
        Document(id="doc1", content="A", metadata={}),
        Document(id="doc2", content="B", metadata={}),
        Document(id="doc3", content="C", metadata={}),
    ]
    relevant = ["doc1", "doc3"]

    metrics = await evaluator.evaluate_retrieval("query", retrieved, relevant)

    assert metrics["precision@1"] == 1.0
    assert metrics["precision@3"] == 2 / 3
    assert metrics["recall@3"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["ndcg@3"] > 0.0


@pytest.mark.asyncio
async def test_generation_metrics_fallback(monkeypatch):
    config = MonitoringConfigV2(
        track_generation_metrics=True,
        faithfulness_enabled=True,
        answer_relevancy_enabled=True,
        context_precision_enabled=True,
        context_recall_enabled=True,
        answer_correctness_enabled=True,
    )
    evaluator = RAGEvaluator(config)

    async def fake_ragas(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "ragkit.evaluation.evaluator._evaluate_with_ragas",
        fake_ragas,
    )

    metrics = await evaluator.evaluate_generation(
        query="When was Python created?",
        response="Python was created in 1991.",
        context=["Python was created in 1991 by Guido van Rossum."],
        ground_truth="Python was created in 1991 by Guido van Rossum.",
    )

    assert "faithfulness" in metrics
    assert "answer_relevancy" in metrics
    assert "context_precision" in metrics
    assert "context_recall" in metrics
    assert "answer_correctness" in metrics
