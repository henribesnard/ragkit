"""Response validation for LLM outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ragkit.config.schema_v2 import LLMGenerationConfigV2
from ragkit.generation.utils.faithfulness import compute_faithfulness
from ragkit.generation.utils.filters import check_filter


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]
    faithfulness_score: float | None = None


class ResponseValidator:
    """Validate LLM responses for citations, faithfulness, and filters."""

    def __init__(self, config: LLMGenerationConfigV2) -> None:
        self.config = config

    async def validate(self, response: str, context: str, query: str) -> ValidationResult:
        issues: list[str] = []
        faithfulness_score: float | None = None

        if self.config.cite_sources and self.config.require_citation_for_facts:
            if not self._has_citations(response):
                issues.append("No citations found")

        if self.config.confidence_threshold > 0:
            faithfulness_score = await compute_faithfulness(response, context, query)
            if faithfulness_score < self.config.confidence_threshold:
                issues.append(f"Low faithfulness: {faithfulness_score:.2f}")

        for filter_type in self.config.content_filters:
            if await check_filter(response, filter_type):
                issues.append(f"Content filter triggered: {filter_type}")

        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            faithfulness_score=faithfulness_score,
        )

    def _has_citations(self, response: str) -> bool:
        if self.config.citation_format == "numbered":
            return bool(re.search(r"\[\d+\]", response))
        if self.config.citation_format == "inline":
            return "source:" in response.lower()
        if self.config.citation_format == "footnote":
            return bool(re.search(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]", response) or re.search(r"\^\d+", response))
        return True
