"""Faithfulness scoring utilities."""

from __future__ import annotations

import re


async def compute_faithfulness(response: str, context: str, query: str) -> float:
    """Compute faithfulness score (best-effort)."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness

        result = evaluate(
            data={
                "question": [query],
                "answer": [response],
                "contexts": [[context]],
            },
            metrics=[faithfulness],
        )
        score = result.get("faithfulness")
        if isinstance(score, list):
            return float(score[0])
        if score is not None:
            return float(score)
    except Exception:
        pass

    return _heuristic_faithfulness(response, context)


def _heuristic_faithfulness(response: str, context: str) -> float:
    response_tokens = _tokenize(response)
    context_tokens = _tokenize(context)
    if not response_tokens:
        return 0.0
    overlap = response_tokens.intersection(context_tokens)
    return len(overlap) / max(len(response_tokens), 1)


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"\b\w+\b", text.lower())
    return set(tokens)
