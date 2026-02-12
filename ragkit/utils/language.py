"""Language detection helpers."""

from __future__ import annotations

try:
    from langdetect import LangDetectException, detect_langs
except Exception:  # pragma: no cover - optional dependency fallback
    detect_langs = None
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


def detect_language(text: str) -> str | None:
    cleaned = (text or "").strip()
    if len(cleaned) < 3 or detect_langs is None:
        return None
    try:
        results = detect_langs(cleaned)
        if not results:
            return None
        best = results[0]
        if best.prob < 0.5:
            return None
        # fr/pt/es/it are hard to distinguish on short text;
        # if top-2 are close romance languages, prefer fr
        if len(results) >= 2 and best.prob - results[1].prob < 0.2:
            romance = {"fr", "pt", "es", "it"}
            candidates = {r.lang for r in results[:3]} & romance
            if "fr" in candidates:
                return "fr"
        return best.lang
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
