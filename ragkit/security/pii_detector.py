"""PII detection and redaction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import re

from ragkit.config.schema_v2 import SecurityConfigV2
from ragkit.security.exceptions import PIIDetectedException

try:  # Optional dependency
    from presidio_analyzer import AnalyzerEngine  # type: ignore
    from presidio_anonymizer import AnonymizerEngine  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    AnalyzerEngine = None
    AnonymizerEngine = None


@dataclass(frozen=True)
class PIIEntity:
    entity_type: str
    start: int
    end: int
    score: float
    value: str | None = None


_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PHONE_NUMBER": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "IP_ADDRESS": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
}


class PIIDetector:
    """Detect and redact PII based on configuration."""

    def __init__(self, config: SecurityConfigV2, language: str = "en") -> None:
        self.config = config
        self.language = language
        self._presidio_available = AnalyzerEngine is not None and AnonymizerEngine is not None

        self.analyzer = AnalyzerEngine() if self._presidio_available else None
        self.anonymizer = AnonymizerEngine() if self._presidio_available else None

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect PII entities in text."""
        if not self.config.pii_detection_enabled:
            return []

        if self._presidio_available:
            entities, _ = self._detect_with_presidio(text)
            return entities

        return self._detect_with_regex(text)

    def detect_and_redact(self, text: str) -> tuple[str, list[PIIEntity]]:
        """Detect PII and apply policy (detect/redact/block)."""
        if not self.config.pii_detection_enabled:
            return text, []

        if self._presidio_available:
            entities, presidio_results = self._detect_with_presidio(text)
            return self._apply_policy(text, entities, presidio_results=presidio_results)

        entities = self._detect_with_regex(text)
        return self._apply_policy(text, entities, presidio_results=None)

    def _apply_policy(
        self,
        text: str,
        entities: list[PIIEntity],
        presidio_results: list[Any] | None,
    ) -> tuple[str, list[PIIEntity]]:
        mode = self.config.pii_detection_mode

        if mode == "block" and entities:
            raise PIIDetectedException(f"PII detected: {entities}")

        if mode == "redact" and entities:
            if self._presidio_available and presidio_results is not None:
                anonymized = self.anonymizer.anonymize(  # type: ignore[union-attr]
                    text=text,
                    analyzer_results=presidio_results,
                )
                return anonymized.text, entities
            return self._redact_with_regex(text, entities), entities

        return text, entities

    def _detect_with_presidio(self, text: str) -> tuple[list[PIIEntity], list[Any]]:
        results = self.analyzer.analyze(  # type: ignore[union-attr]
            text=text,
            language=self.language,
            entities=self.config.pii_entities,
            score_threshold=self.config.pii_confidence_threshold,
        )
        entities = [
            PIIEntity(
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                score=float(result.score),
                value=text[result.start : result.end],
            )
            for result in results
        ]
        return entities, results

    def _detect_with_regex(self, text: str) -> list[PIIEntity]:
        entities: list[PIIEntity] = []
        for entity_type in self.config.pii_entities:
            pattern = _PII_PATTERNS.get(entity_type)
            if not pattern:
                continue
            for match in pattern.finditer(text):
                entities.append(
                    PIIEntity(
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        score=1.0,
                        value=match.group(0),
                    )
                )
        return entities

    def _redact_with_regex(self, text: str, entities: list[PIIEntity]) -> str:
        redacted = text
        for entity_type in self.config.pii_entities:
            pattern = _PII_PATTERNS.get(entity_type)
            if not pattern:
                continue
            redacted = pattern.sub(f"[{entity_type}]", redacted)
        return redacted
