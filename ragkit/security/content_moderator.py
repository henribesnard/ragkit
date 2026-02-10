"""Content moderation utilities (toxicity, prompt injection)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ragkit.config.schema_v2 import SecurityConfigV2
from ragkit.security.exceptions import PromptInjectionException, ToxicContentException

_TOXIC_TERMS = {
    "hate",
    "idiot",
    "stupid",
    "kill",
    "terrorist",
    "worthless",
    "moron",
    "dumb",
}

_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard.*system.*prompt",
    r"you are now",
    r"system prompt",
    r"developer message",
    r"<\|.*\|>",  # special tokens
    r"###.*instruction",
]

_JAILBREAK_PATTERNS = [
    r"\bjailbreak\b",
    r"\bdo anything now\b",
    r"\bdan\b",
    r"\bunlock\b",
]


@dataclass(frozen=True)
class ModerationResult:
    toxicity_score: float | None
    flags: list[str]
    details: dict[str, Any]


class ContentModerator:
    """Moderate content for toxicity and prompt injection."""

    def __init__(self, config: SecurityConfigV2) -> None:
        self.config = config
        self._toxicity_model: Any | None = None
        self._detoxify_available: bool | None = None

    def check_toxicity(self, text: str) -> dict[str, float]:
        if not self.config.content_moderation_enabled:
            return {"toxicity": 0.0}

        model = self._get_detoxify_model()
        if model is not None:
            scores = model.predict(text)
            toxicity = float(scores.get("toxicity", 0.0))
            if toxicity > self.config.toxicity_threshold:
                raise ToxicContentException(
                    f"Toxic content detected (score: {toxicity:.2f})"
                )
            return {k: float(v) for k, v in scores.items()}

        lowered = text.lower()
        found = [term for term in _TOXIC_TERMS if term in lowered]
        toxicity = 1.0 if found else 0.0
        if toxicity > self.config.toxicity_threshold:
            raise ToxicContentException("Toxic content detected")
        return {"toxicity": toxicity}

    def check_prompt_injection(self, text: str) -> bool:
        if not self.config.content_moderation_enabled:
            return False

        lowered = text.lower()
        if self.config.block_prompt_injection:
            for pattern in _INJECTION_PATTERNS:
                if re.search(pattern, lowered, re.IGNORECASE):
                    raise PromptInjectionException(f"Injection detected: {pattern}")

        if self.config.block_jailbreak_attempts:
            for pattern in _JAILBREAK_PATTERNS:
                if re.search(pattern, lowered, re.IGNORECASE):
                    raise PromptInjectionException(f"Jailbreak detected: {pattern}")

        return False

    def moderate(self, text: str) -> ModerationResult:
        flags: list[str] = []
        details: dict[str, Any] = {}
        toxicity_score: float | None = None

        try:
            scores = self.check_toxicity(text)
            toxicity_score = float(scores.get("toxicity", 0.0))
            details["toxicity"] = scores
        except ToxicContentException:
            flags.append("toxicity")
            raise

        try:
            self.check_prompt_injection(text)
        except PromptInjectionException:
            flags.append("prompt_injection")
            raise

        return ModerationResult(toxicity_score=toxicity_score, flags=flags, details=details)

    def _get_detoxify_model(self) -> Any | None:
        if self._detoxify_available is False:
            return None

        if self._toxicity_model is not None:
            return self._toxicity_model

        try:
            from detoxify import Detoxify  # type: ignore

            self._toxicity_model = Detoxify("original")
            self._detoxify_available = True
            return self._toxicity_model
        except Exception:
            self._detoxify_available = False
            return None
