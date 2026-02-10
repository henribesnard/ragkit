"""Fusion methods for hybrid retrieval."""

from __future__ import annotations

from collections import defaultdict

from ragkit.retrieval.base_retriever import SearchResult
from ragkit.retrieval.utils.normalizers import normalize_scores


def reciprocal_rank_fusion(
    results_lists: list[list[SearchResult]],
    k: int = 60,
) -> list[SearchResult]:
    """Fuse multiple result lists using Reciprocal Rank Fusion (RRF).

    RRF is more robust than score-based fusion as it uses ranks instead of raw scores.

    Formula: score_rrf(doc) = Σ 1 / (k + rank_i(doc))

    Args:
        results_lists: List of result lists from different retrievers
        k: RRF constant (typically 60)

    Returns:
        Merged and sorted results
    """
    rrf_scores = defaultdict(float)
    doc_map = {}  # Map chunk ID to SearchResult

    for results in results_lists:
        for rank, result in enumerate(results, start=1):
            chunk_id = result.chunk.id
            rrf_scores[chunk_id] += 1.0 / (k + rank)

            # Store the result object (keep first occurrence)
            if chunk_id not in doc_map:
                doc_map[chunk_id] = result

    # Sort by RRF score (descending)
    merged = sorted(
        [
            SearchResult(
                chunk=doc_map[chunk_id].chunk,
                score=rrf_score,
                metadata=doc_map[chunk_id].metadata,
            )
            for chunk_id, rrf_score in rrf_scores.items()
        ],
        key=lambda x: x.score,
        reverse=True,
    )

    return merged


def linear_fusion(
    semantic_results: list[SearchResult],
    lexical_results: list[SearchResult],
    alpha: float = 0.5,
    normalize: bool = True,
    normalization_method: str = "min-max",
) -> list[SearchResult]:
    """Fuse results using linear interpolation.

    Formula: score = alpha * sem_score + (1-alpha) * lex_score

    Args:
        semantic_results: Results from semantic retriever
        lexical_results: Results from lexical retriever
        alpha: Weight for semantic (0.0 = full lexical, 1.0 = full semantic)
        normalize: Whether to normalize scores first
        normalization_method: Normalization method

    Returns:
        Merged and sorted results
    """
    # Create score maps
    sem_scores = {r.chunk.id: r.score for r in semantic_results}
    lex_scores = {r.chunk.id: r.score for r in lexical_results}

    # Normalize scores if requested
    if normalize:
        if sem_scores:
            sem_score_list = list(sem_scores.values())
            normalized_sem = normalize_scores(sem_score_list, method=normalization_method)
            sem_scores = {
                chunk_id: norm_score
                for chunk_id, norm_score in zip(
                    sem_scores.keys(),
                    normalized_sem,
                    strict=False,
                )
            }

        if lex_scores:
            lex_score_list = list(lex_scores.values())
            normalized_lex = normalize_scores(lex_score_list, method=normalization_method)
            lex_scores = {
                chunk_id: norm_score
                for chunk_id, norm_score in zip(
                    lex_scores.keys(),
                    normalized_lex,
                    strict=False,
                )
            }

    # Combine scores
    all_chunk_ids = set(sem_scores.keys()) | set(lex_scores.keys())
    doc_map = {}

    # Build document map
    for result in semantic_results + lexical_results:
        if result.chunk.id not in doc_map:
            doc_map[result.chunk.id] = result

    # Calculate combined scores
    merged = []
    for chunk_id in all_chunk_ids:
        sem_score = sem_scores.get(chunk_id, 0.0)
        lex_score = lex_scores.get(chunk_id, 0.0)

        # Linear interpolation
        combined_score = alpha * sem_score + (1 - alpha) * lex_score

        merged.append(
            SearchResult(
                chunk=doc_map[chunk_id].chunk,
                score=combined_score,
                metadata=doc_map[chunk_id].metadata,
            )
        )

    # Sort by combined score (descending)
    merged.sort(key=lambda x: x.score, reverse=True)

    return merged


def weighted_sum_fusion(
    results_lists: list[list[SearchResult]],
    weights: list[float] | None = None,
    normalize: bool = True,
    normalization_method: str = "min-max",
) -> list[SearchResult]:
    """Fuse results using weighted sum.

    Args:
        results_lists: List of result lists
        weights: Weights for each list (must sum to 1.0)
        normalize: Whether to normalize scores first
        normalization_method: Normalization method

    Returns:
        Merged and sorted results
    """
    if weights is None:
        # Equal weights
        weights = [1.0 / len(results_lists)] * len(results_lists)

    if len(weights) != len(results_lists):
        raise ValueError("Number of weights must match number of result lists")

    if abs(sum(weights) - 1.0) > 1e-6:
        raise ValueError("Weights must sum to 1.0")

    # Collect all scores
    score_maps = []
    doc_map = {}

    for results in results_lists:
        scores = {r.chunk.id: r.score for r in results}

        # Normalize if requested
        if normalize and scores:
            score_list = list(scores.values())
            normalized = normalize_scores(score_list, method=normalization_method)
            scores = {
                chunk_id: norm
                for chunk_id, norm in zip(
                    scores.keys(),
                    normalized,
                    strict=False,
                )
            }

        score_maps.append(scores)

        # Build document map
        for result in results:
            if result.chunk.id not in doc_map:
                doc_map[result.chunk.id] = result

    # Combine scores
    all_chunk_ids = set()
    for scores in score_maps:
        all_chunk_ids.update(scores.keys())

    merged = []
    for chunk_id in all_chunk_ids:
        # Weighted sum
        combined_score = sum(
            weight * score_map.get(chunk_id, 0.0)
            for weight, score_map in zip(weights, score_maps, strict=False)
        )

        merged.append(
            SearchResult(
                chunk=doc_map[chunk_id].chunk,
                score=combined_score,
                metadata=doc_map[chunk_id].metadata,
            )
        )

    # Sort by combined score (descending)
    merged.sort(key=lambda x: x.score, reverse=True)

    return merged
