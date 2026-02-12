"""Score fusion utilities for retrieval."""

from __future__ import annotations

from collections import defaultdict

from ragkit.config.schema import FusionConfig
from ragkit.models import RetrievalResult


class ScoreFusion:
    @staticmethod
    def weighted_sum(
        results_by_type: dict[str, list[RetrievalResult]],
        weights: dict[str, float],
        normalize: bool = True,
    ) -> list[RetrievalResult]:
        combined_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievalResult] = {}

        for retrieval_type, results in results_by_type.items():
            if not results:
                continue
            weight = weights.get(retrieval_type, 1.0)
            scores = [result.score for result in results]
            max_score = max(scores) if scores else 1.0
            for result in results:
                score = result.score
                if normalize and max_score > 0:
                    score = score / max_score
                combined_scores[result.chunk.id] += score * weight
                if (
                    result.chunk.id not in chunk_map
                    or result.score > chunk_map[result.chunk.id].score
                ):
                    chunk_map[result.chunk.id] = result

        fused: list[RetrievalResult] = []
        for chunk_id, score in combined_scores.items():
            original = chunk_map[chunk_id]
            fused.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=score,
                    retrieval_type="fusion",
                )
            )

        fused.sort(key=lambda item: item.score, reverse=True)
        return fused

    @staticmethod
    def reciprocal_rank_fusion(
        results_by_type: dict[str, list[RetrievalResult]],
        k: int = 60,
    ) -> list[RetrievalResult]:
        combined_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievalResult] = {}

        for results in results_by_type.values():
            if not results:
                continue
            ordered = sorted(results, key=lambda item: item.score, reverse=True)
            for rank, result in enumerate(ordered, start=1):
                combined_scores[result.chunk.id] += 1.0 / (k + rank)
                if (
                    result.chunk.id not in chunk_map
                    or result.score > chunk_map[result.chunk.id].score
                ):
                    chunk_map[result.chunk.id] = result

        fused: list[RetrievalResult] = []
        for chunk_id, score in combined_scores.items():
            original = chunk_map[chunk_id]
            fused.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=score,
                    retrieval_type="fusion",
                )
            )

        fused.sort(key=lambda item: item.score, reverse=True)
        return fused

    @staticmethod
    def apply(
        results_by_type: dict[str, list[RetrievalResult]],
        config: FusionConfig,
        weights: dict[str, float],
    ) -> list[RetrievalResult]:
        if config.method == "weighted_sum":
            return ScoreFusion.weighted_sum(
                results_by_type, weights, normalize=config.normalize_scores
            )
        if config.method == "reciprocal_rank_fusion":
            return ScoreFusion.reciprocal_rank_fusion(results_by_type, k=config.rrf_k)
        raise ValueError(f"Unknown fusion method: {config.method}")
