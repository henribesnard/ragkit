"""Prometheus-backed metrics collector."""

from __future__ import annotations

from typing import Any


class MonitoringMetricsCollector:
    """Collect runtime metrics and expose to Prometheus when available."""

    def __init__(self) -> None:
        self._init_prometheus()
        self._last_values: dict[str, Any] = {}

    def record_latency(self, latency_seconds: float) -> None:
        if self.latency_histogram:
            self.latency_histogram.observe(latency_seconds)
        self._last_values["latency_seconds"] = latency_seconds

    def record_throughput(self) -> None:
        if self.query_counter:
            self.query_counter.inc()
        self._last_values["queries_total"] = self._last_values.get("queries_total", 0) + 1

    def record_faithfulness(self, score: float) -> None:
        if self.faithfulness_gauge:
            self.faithfulness_gauge.set(score)
        self._last_values["faithfulness"] = score

    def record_cost(self, component: str, cost_usd: float) -> None:
        if self.cost_counter:
            self.cost_counter.labels(component=component).inc(cost_usd)
        costs = self._last_values.setdefault("cost_usd", {})
        costs[component] = costs.get(component, 0.0) + cost_usd

    def record_retrieval_metrics(self, metrics: dict[str, float]) -> None:
        for name, value in metrics.items():
            if self.retrieval_gauges and name in self.retrieval_gauges:
                self.retrieval_gauges[name].set(value)
        self._last_values["retrieval_metrics"] = metrics

    def snapshot(self) -> dict[str, Any]:
        return dict(self._last_values)

    def _init_prometheus(self) -> None:
        self.latency_histogram = None
        self.query_counter = None
        self.faithfulness_gauge = None
        self.cost_counter = None
        self.retrieval_gauges: dict[str, Any] = {}

        try:
            from prometheus_client import Counter, Gauge, Histogram  # type: ignore
        except Exception:
            return

        self.latency_histogram = Histogram(
            "rag_query_latency_seconds",
            "Query latency in seconds",
            buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10],
        )
        self.query_counter = Counter("rag_queries_total", "Total queries")
        self.faithfulness_gauge = Gauge("rag_faithfulness", "Faithfulness score")
        self.cost_counter = Counter(
            "rag_cost_usd_total",
            "Total cost in USD",
            ["component"],
        )
        self.retrieval_gauges = {
            "precision@5": Gauge("rag_precision_at_5", "Precision at 5"),
            "recall@10": Gauge("rag_recall_at_10", "Recall at 10"),
            "mrr": Gauge("rag_mrr", "Mean reciprocal rank"),
        }
