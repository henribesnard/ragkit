"""Context compression helpers."""

from __future__ import annotations

from typing import Any


def compress_context(text: str, ratio: float = 0.5, tokenizer: Any | None = None) -> str:
    """Compress context to a target ratio (best-effort)."""
    if ratio >= 1.0:
        return text

    try:
        from llmlingua import PromptCompressor

        compressor = PromptCompressor()
        target_tokens = int(_token_count(text, tokenizer) * ratio)
        result = compressor.compress(prompt=text, target_token=target_tokens)
        return result.get("compressed_prompt", text)
    except Exception:
        return _truncate_by_ratio(text, ratio, tokenizer)


def _truncate_by_ratio(text: str, ratio: float, tokenizer: Any | None) -> str:
    tokens = _tokenize(text, tokenizer)
    target = max(1, int(len(tokens) * ratio))
    return _detokenize(tokens[:target], tokenizer)


def _token_count(text: str, tokenizer: Any | None) -> int:
    return len(_tokenize(text, tokenizer))


def _tokenize(text: str, tokenizer: Any | None) -> list[Any]:
    if tokenizer is None:
        return text.split()
    return tokenizer.encode(text)


def _detokenize(tokens: list[Any], tokenizer: Any | None) -> str:
    if tokenizer is None:
        return " ".join(str(tok) for tok in tokens)
    return tokenizer.decode(tokens)
