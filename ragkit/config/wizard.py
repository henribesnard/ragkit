"""Wizard logic and shared models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ragkit.config.profiles import get_profile_description, get_profile_for_answers
from ragkit.config.schema_v2 import WizardProfileConfig


class WizardAnswers(BaseModel):
    """Answers collected from the wizard questionnaire."""

    model_config = ConfigDict(extra="forbid")

    kb_type: Literal[
        "technical_documentation",
        "faq_support",
        "legal_regulatory",
        "reports_analysis",
        "general_knowledge",
    ]

    has_tables_diagrams: bool = False
    needs_multi_document: bool = False
    large_documents: bool = False
    needs_precision: bool = False
    frequent_updates: bool = False
    cite_page_numbers: bool = False


class WizardAnalysis(BaseModel):
    """Result returned by the wizard analysis."""

    model_config = ConfigDict(extra="forbid")

    profile_name: str
    description: str
    config_summary: dict[str, str]
    full_config: dict[str, Any]


def build_profile_name(answers: WizardAnswers) -> str:
    """Create a readable profile name based on answers."""
    profile_name = answers.kb_type.replace("_", " ").title()
    if answers.needs_precision:
        profile_name += " (Max Precision)"
    elif answers.large_documents:
        profile_name += " (Long Docs)"
    return profile_name


def build_profile_config(answers: WizardAnswers) -> WizardProfileConfig:
    """Create a WizardProfileConfig from the wizard answers."""
    profile = get_profile_for_answers(
        kb_type=answers.kb_type,
        has_tables=answers.has_tables_diagrams,
        needs_multi_doc=answers.needs_multi_document,
        large_docs=answers.large_documents,
        needs_precision=answers.needs_precision,
        frequent_updates=answers.frequent_updates,
        cite_pages=answers.cite_page_numbers,
    )

    return WizardProfileConfig(
        knowledge_base_type=answers.kb_type,
        has_tables_diagrams=answers.has_tables_diagrams,
        needs_multi_document=answers.needs_multi_document,
        large_documents=answers.large_documents,
        needs_precision=answers.needs_precision,
        frequent_updates=answers.frequent_updates,
        cite_page_numbers=answers.cite_page_numbers,
        detected_profile_name=build_profile_name(answers),
        recommended_config=profile,
    )


def analyze_answers(answers: WizardAnswers) -> WizardAnalysis:
    """Analyze wizard answers and return a ready-to-display summary."""
    profile = get_profile_for_answers(
        kb_type=answers.kb_type,
        has_tables=answers.has_tables_diagrams,
        needs_multi_doc=answers.needs_multi_document,
        large_docs=answers.large_documents,
        needs_precision=answers.needs_precision,
        frequent_updates=answers.frequent_updates,
        cite_pages=answers.cite_page_numbers,
    )

    summary = {
        "chunking": _format_chunking_summary(profile.get("chunking", {})),
        "retrieval": _format_retrieval_summary(profile.get("retrieval", {})),
        "reranking": "enabled" if profile.get("reranking", {}).get("enabled") else "disabled",
        "parsing": _format_parsing_summary(profile.get("parsing", {})),
    }

    return WizardAnalysis(
        profile_name=build_profile_name(answers),
        description=get_profile_description(answers.kb_type, profile),
        config_summary=summary,
        full_config=profile,
    )


def _format_chunking_summary(chunking: dict[str, Any]) -> str:
    strategy = chunking.get("strategy", "fixed")
    size = chunking.get("chunk_size") or chunking.get("child_chunk_size") or "?"
    overlap = chunking.get("chunk_overlap", "?")
    return f"{strategy} ({size} tokens, overlap {overlap})"


def _format_retrieval_summary(retrieval: dict[str, Any]) -> str:
    architecture = retrieval.get("architecture", "semantic")
    top_k = retrieval.get("top_k", "?")
    return f"{architecture} (top_k = {top_k})"


def _format_parsing_summary(parsing: dict[str, Any]) -> str:
    features = []
    if parsing.get("table_extraction"):
        features.append("tables")
    if parsing.get("ocr_enabled"):
        features.append("ocr")
    if parsing.get("image_captioning"):
        features.append("images")
    return " + ".join(features) if features else "standard"
