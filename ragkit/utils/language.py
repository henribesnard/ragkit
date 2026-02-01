"""Language detection helpers."""

from __future__ import annotations

from typing import Optional

try:
    from langdetect import LangDetectException, detect
except Exception:  # pragma: no cover - optional dependency fallback
    detect = None
    LangDetectException = Exception


_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
}


def detect_language(text: str) -> Optional[str]:
    cleaned = (text or "").strip()
    if len(cleaned) < 3 or detect is None:
        return None
    try:
        return detect(cleaned)
    except LangDetectException:
        return None
    except Exception:
        return None


def language_name(code: str) -> str:
    normalized = (code or "").strip().lower()
    if not normalized:
        return code
    base = normalized.split("-")[0]
    return _LANGUAGE_NAMES.get(base, code)
