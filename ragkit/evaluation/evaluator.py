"""Evaluation utilities for retrieval and generation metrics."""

from __future__ import annotations

import inspect
import math
import re
from typing import Any

from ragkit.config.schema_v2 import MonitoringConfigV2
from ragkit.generation.utils.faithfulness import compute_faithfulness


class RAGEvaluator:
    """Evaluate retrieval and generation quality."""

    def __init__(self, config: MonitoringConfigV2) -> None:
        self.config = config

    async def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: list[Any],
        relevant_doc_ids: list[str],
    ) -> dict[str, float]:
        """Compute retrieval metrics."""
        _ = query
        retrieved_ids = [_extract_doc_id(doc) for doc in retrieved_docs]
        relevant_set = {str(doc_id) for doc_id in relevant_doc_ids}
        metrics: dict[str, float] = {}

        for k in self.config.precision_at_k:
            metrics[f"precision@{k}"] = _precision_at_k(retrieved_ids, relevant_set, k)

        for k in self.config.recall_at_k:
            metrics[f"recall@{k}"] = _recall_at_k(retrieved_ids, relevant_set, k)

        if self.config.track_mrr:
            metrics["mrr"] = _mrr(retrieved_ids, relevant_set)

        if self.config.track_ndcg:
            for k in set(self.config.precision_at_k + self.config.recall_at_k):
                metrics[f"ndcg@{k}"] = _ndcg_at_k(retrieved_ids, relevant_set, k)

        return metrics

    async def evaluate_generation(
        self,
        query: str,
        response: str,
        context: list[str],
        ground_truth: str | None = None,
    ) -> dict[str, float]:
        """Compute generation metrics (RAGAS or heuristic fallback)."""
        if not self.config.track_generation_metrics:
            return {}

        metrics = await _evaluate_with_ragas(
            query=query,
            response=response,
            context=context,
            config=self.config,
        )
        if metrics is None:
            metrics = await _heuristic_generation_metrics(
                query=query,
                response=response,
                context=context,
                config=self.config,
                ground_truth=ground_truth,
            )

        return metrics


def _extract_doc_id(doc: Any) -> str:
    if doc is None:
        return ""
    if hasattr(doc, "id"):
        return str(getattr(doc, "id"))
    if hasattr(doc, "document_id"):
        return str(getattr(doc, "document_id"))
    if hasattr(doc, "chunk"):
        chunk = getattr(doc, "chunk")
        if hasattr(chunk, "document_id"):
            return str(getattr(chunk, "document_id"))
        if hasattr(chunk, "id"):
            return str(getattr(chunk, "id"))
    if hasattr(doc, "metadata"):
        metadata = getattr(doc, "metadata") or {}
        if isinstance(metadata, dict):
            for key in ("document_id", "doc_id", "id", "source_id"):
                if key in metadata:
                    return str(metadata[key])
    if isinstance(doc, dict):
        for key in ("id", "document_id", "doc_id"):
            if key in doc:
                return str(doc[key])
    return str(doc)


def _precision_at_k(retrieved_ids: list[str], relevant_set: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_in_top_k = len(set(top_k) & relevant_set)
    return relevant_in_top_k / k


def _recall_at_k(retrieved_ids: list[str], relevant_set: set[str], k: int) -> float:
    if not relevant_set:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_in_top_k = len(set(top_k) & relevant_set)
    return relevant_in_top_k / len(relevant_set)


def _mrr(retrieved_ids: list[str], relevant_set: set[str]) -> float:
    for idx, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_set:
            return 1.0 / idx
    return 0.0


def _ndcg_at_k(retrieved_ids: list[str], relevant_set: set[str], k: int) -> float:
    if not relevant_set or k <= 0:
        return 0.0
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in relevant_set:
            dcg += 1.0 / math.log2(i + 1)
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if idcg == 0:
        return 0.0
    return dcg / idcg


async def _evaluate_with_ragas(
    query: str,
    response: str,
    context: list[str],
    config: MonitoringConfigV2,
) -> dict[str, float] | None:
    try:
        from ragas import evaluate  # type: ignore
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )  # type: ignore
    except Exception:
        return None

    metrics_to_compute = []
    if config.faithfulness_enabled:
        metrics_to_compute.append(faithfulness)
    if config.answer_relevancy_enabled:
        metrics_to_compute.append(answer_relevancy)
    if config.context_precision_enabled:
        metrics_to_compute.append(context_precision)
    if config.context_recall_enabled:
        metrics_to_compute.append(context_recall)

    if not metrics_to_compute:
        return {}

    dataset = {
        "question": [query],
        "answer": [response],
        "contexts": [context],
    }

    result = evaluate(dataset, metrics=metrics_to_compute)
    if inspect.iscoroutine(result):
        result = await result

    metrics: dict[str, float] = {}
    for key in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        value = result.get(key)
        if isinstance(value, list):
            metrics[key] = float(value[0])
        elif value is not None:
            metrics[key] = float(value)
    return metrics


async def _heuristic_generation_metrics(
    query: str,
    response: str,
    context: list[str],
    config: MonitoringConfigV2,
    ground_truth: str | None = None,
) -> dict[str, float]:
    metrics: dict[str, float] = {}
    response_tokens = _tokenize(response)
    query_tokens = _tokenize(query)
    context_tokens = _tokenize(" ".join(context))

    if config.faithfulness_enabled:
        metrics["faithfulness"] = await compute_faithfulness(response, " ".join(context), query)
    if config.answer_relevancy_enabled:
        metrics["answer_relevancy"] = _jaccard(query_tokens, response_tokens)
    if config.context_precision_enabled:
        metrics["context_precision"] = _precision_overlap(response_tokens, context_tokens)
    if config.context_recall_enabled:
        metrics["context_recall"] = _recall_overlap(response_tokens, context_tokens)
    if config.answer_correctness_enabled and ground_truth:
        metrics["answer_correctness"] = _jaccard(response_tokens, _tokenize(ground_truth))

    return metrics


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _precision_overlap(response_tokens: set[str], context_tokens: set[str]) -> float:
    if not response_tokens:
        return 0.0
    return len(response_tokens & context_tokens) / len(response_tokens)


def _recall_overlap(response_tokens: set[str], context_tokens: set[str]) -> float:
    if not context_tokens:
        return 0.0
    return len(response_tokens & context_tokens) / len(context_tokens)
