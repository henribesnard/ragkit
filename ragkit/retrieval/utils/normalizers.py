"""Score normalization utilities."""

from __future__ import annotations

import numpy as np


def normalize_scores(
    scores: list[float],
    method: str = "min-max",
) -> list[float]:
    """Normalize scores to a common scale.

    Args:
        scores: List of scores to normalize
        method: Normalization method ("min-max", "z-score", "softmax")

    Returns:
        Normalized scores
    """
    if not scores:
        return []

    scores_array = np.array(scores)

    if method == "min-max":
        # Scale to [0, 1]
        min_score = scores_array.min()
        max_score = scores_array.max()

        if max_score == min_score:
            # All scores are the same
            return [1.0] * len(scores)

        normalized = (scores_array - min_score) / (max_score - min_score)
        return normalized.tolist()

    elif method == "z-score":
        # Standardization (mean=0, std=1)
        mean = scores_array.mean()
        std = scores_array.std()

        if std == 0:
            # All scores are the same
            return [0.0] * len(scores)

        normalized = (scores_array - mean) / std
        return normalized.tolist()

    elif method == "softmax":
        # Softmax: converts to probability distribution
        exp_scores = np.exp(scores_array - scores_array.max())  # Subtract max for stability
        softmax = exp_scores / exp_scores.sum()
        return softmax.tolist()

    else:
        raise ValueError(f"Unknown normalization method: {method}")


def min_max_normalize(scores: list[float]) -> list[float]:
    """Min-max normalization to [0, 1]."""
    return normalize_scores(scores, method="min-max")


def z_score_normalize(scores: list[float]) -> list[float]:
    """Z-score normalization (standardization)."""
    return normalize_scores(scores, method="z-score")


def softmax_normalize(scores: list[float]) -> list[float]:
    """Softmax normalization (probability distribution)."""
    return normalize_scores(scores, method="softmax")
