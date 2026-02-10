"""Maximal Marginal Relevance (MMR) for diversity-aware retrieval."""

from __future__ import annotations

import numpy as np

from ragkit.retrieval.base_retriever import SearchResult


def maximal_marginal_relevance(
    query_embedding: np.ndarray,
    results: list[SearchResult],
    embeddings: list[np.ndarray],
    lambda_param: float = 0.5,
    top_k: int = 10,
    diversity_threshold: float = 0.8,
) -> list[SearchResult]:
    """Select documents using Maximal Marginal Relevance.

    MMR balances relevance and diversity by selecting documents that are:
    1. Relevant to the query
    2. Diverse from already selected documents

    Formula:
        MMR = arg max [λ × Sim(doc, query) - (1-λ) × max(Sim(doc, doc_selected))]
              doc ∈ R \\ S

    Args:
        query_embedding: Query embedding vector
        results: List of search results (sorted by relevance)
        embeddings: Corresponding embeddings for each result
        lambda_param: Balance parameter (0.0 = max diversity, 1.0 = max relevance)
        top_k: Number of documents to select
        diversity_threshold: Maximum similarity allowed between selected docs

    Returns:
        List of selected SearchResults, ordered by MMR score
    """
    if not results or not embeddings:
        return []

    if len(results) != len(embeddings):
        raise ValueError("Number of results must match number of embeddings")

    # Compute relevance scores (similarity to query)
    relevance_scores = [cosine_similarity(query_embedding, emb) for emb in embeddings]

    # Initialize
    selected_indices = []
    remaining_indices = list(range(len(results)))

    # Step 1: Select most relevant document
    first_idx = np.argmax(relevance_scores)
    selected_indices.append(first_idx)
    remaining_indices.remove(first_idx)

    # Step 2: Iteratively select documents maximizing MMR
    while len(selected_indices) < min(top_k, len(results)) and remaining_indices:
        mmr_scores = []

        for idx in remaining_indices:
            # Relevance to query
            relevance = relevance_scores[idx]

            # Diversity from selected documents (max similarity)
            max_similarity = max(
                cosine_similarity(embeddings[idx], embeddings[sel_idx])
                for sel_idx in selected_indices
            )

            # MMR score
            mmr = lambda_param * relevance - (1 - lambda_param) * max_similarity
            mmr_scores.append((idx, mmr, max_similarity))

        # Select document with highest MMR
        best_idx, best_mmr, max_sim = max(mmr_scores, key=lambda x: x[1])

        # Check diversity threshold
        if max_sim <= diversity_threshold:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        else:
            # All remaining docs are too similar, stop
            break

    # Return selected results in MMR order
    return [results[idx] for idx in selected_indices]


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity in [0, 1] (assuming normalized vectors)
    """
    # Ensure vectors are 1D
    vec1 = vec1.flatten()
    vec2 = vec2.flatten()

    # Compute dot product (assumes vectors are L2 normalized)
    dot_product = np.dot(vec1, vec2)

    # Compute norms
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0

    # Cosine similarity
    similarity = dot_product / (norm1 * norm2)

    # Clip to [0, 1] (cosine can be [-1, 1], but for embeddings usually [0, 1])
    return float(np.clip(similarity, 0.0, 1.0))


def diversify_results(
    results: list[SearchResult],
    embeddings: list[np.ndarray],
    diversity_threshold: float = 0.8,
    max_results: int = 10,
) -> list[SearchResult]:
    """Diversify results by removing highly similar documents.

    Args:
        results: List of search results
        embeddings: Corresponding embeddings
        diversity_threshold: Maximum similarity allowed
        max_results: Maximum number of results to return

    Returns:
        Diversified results
    """
    if not results:
        return []

    selected = [0]  # Start with top result
    selected_embeddings = [embeddings[0]]

    for i in range(1, len(results)):
        # Check similarity with all selected documents
        similarities = [
            cosine_similarity(embeddings[i], sel_emb) for sel_emb in selected_embeddings
        ]

        # If not too similar to any selected doc, add it
        if max(similarities) <= diversity_threshold:
            selected.append(i)
            selected_embeddings.append(embeddings[i])

            if len(selected) >= max_results:
                break

    return [results[idx] for idx in selected]
