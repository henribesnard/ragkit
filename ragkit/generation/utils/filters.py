"""Content filters for LLM outputs."""

from __future__ import annotations

import re


async def check_filter(text: str, filter_type: str) -> bool:
    """Check if text violates a filter."""
    if filter_type == "toxicity":
        return _contains_toxicity(text)
    if filter_type == "pii":
        return _contains_pii(text)
    if filter_type == "prompt_injection":
        return _contains_prompt_injection(text)
    return False


def _contains_toxicity(text: str) -> bool:
    try:
        from detoxify import Detoxify

        model = Detoxify("original")
        scores = model.predict(text)
        return float(scores.get("toxicity", 0.0)) > 0.8
    except Exception:
        toxic_terms = {"hate", "idiot", "stupid", "kill", "terrorist"}
        lowered = text.lower()
        return any(term in lowered for term in toxic_terms)


def _contains_pii(text: str) -> bool:
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    iban_pattern = r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"
    credit_card_pattern = r"\b(?:\d[ -]*?){13,16}\b"

    patterns = [
        email_pattern,
        ssn_pattern,
        phone_pattern,
        iban_pattern,
        credit_card_pattern,
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _contains_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    triggers = [
        "ignore previous instructions",
        "disregard previous instructions",
        "system prompt",
        "developer message",
        "act as",
        "jailbreak",
    ]
    return any(trigger in lowered for trigger in triggers)
