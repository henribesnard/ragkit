"""Predefined configuration profiles for the wizard."""

from __future__ import annotations

from typing import Any

PROFILES: dict[str, dict[str, Any]] = {
    "technical_documentation": {
        "description": "Technical documentation, APIs, and code",
        "chunking": {
            "strategy": "semantic",
            "chunk_size": 512,
            "chunk_overlap": 64,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.3,
            "top_k": 10,
        },
        "reranking": {
            "enabled": True,
        },
        "parsing": {
            "table_extraction": True,
            "code_block_detection": True,
            "ocr_enabled": False,
        },
        "llm": {
            "temperature": 0.2,
            "cite_sources": True,
        },
    },
    "faq_support": {
        "description": "FAQ, customer support, and Q&A",
        "chunking": {
            "strategy": "paragraph_based",
            "chunk_size": 256,
            "chunk_overlap": 50,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.8,
            "top_k": 5,
        },
        "reranking": {
            "enabled": False,
        },
        "parsing": {
            "table_extraction": False,
            "header_detection": True,
        },
        "llm": {
            "temperature": 0.7,
            "cite_sources": False,
        },
    },
    "legal_regulatory": {
        "description": "Legal, compliance, and regulatory documents",
        "chunking": {
            "strategy": "parent_child",
            "parent_chunk_size": 1500,
            "child_chunk_size": 400,
            "chunk_overlap": 100,
        },
        "retrieval": {
            "architecture": "hybrid_rerank",
            "alpha": 0.5,
            "top_k": 20,
        },
        "reranking": {
            "enabled": True,
            "multi_stage": True,
        },
        "parsing": {
            "preserve_structure": True,
            "header_detection": True,
            "footer_removal": True,
        },
        "llm": {
            "temperature": 0.0,
            "cite_sources": True,
            "citation_format": "footnote",
        },
        "metadata": {
            "add_page_numbers": True,
            "add_section_titles": True,
        },
    },
    "reports_analysis": {
        "description": "Reports, analytics, and financial statements",
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 800,
            "chunk_overlap": 100,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.4,
            "top_k": 15,
        },
        "reranking": {
            "enabled": True,
        },
        "parsing": {
            "table_extraction": True,
            "table_strategy": "vision",
            "image_captioning": True,
            "header_detection": True,
        },
        "llm": {
            "temperature": 0.3,
            "cite_sources": True,
        },
    },
    "general_knowledge": {
        "description": "General knowledge base",
        "chunking": {
            "strategy": "fixed_size",
            "chunk_size": 512,
            "chunk_overlap": 50,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.6,
            "top_k": 8,
        },
        "reranking": {
            "enabled": False,
        },
        "parsing": {
            "table_extraction": False,
            "ocr_enabled": False,
        },
        "llm": {
            "temperature": 0.5,
            "cite_sources": True,
        },
    },
}


def get_profile_for_answers(
    kb_type: str,
    has_tables: bool,
    needs_multi_doc: bool,
    large_docs: bool,
    needs_precision: bool,
    frequent_updates: bool,
    cite_pages: bool,
) -> dict[str, Any]:
    """Generate a profile configuration based on wizard answers."""
    if kb_type not in PROFILES:
        raise ValueError(f"Unknown knowledge base type: {kb_type}")

    import copy

    profile: dict[str, Any] = copy.deepcopy(PROFILES[kb_type])

    if has_tables:
        profile.setdefault("parsing", {})
        profile["parsing"]["table_extraction"] = True
        profile["parsing"]["table_strategy"] = "vision"
        profile["parsing"]["header_detection"] = True

    if needs_multi_doc:
        profile.setdefault("retrieval", {})
        profile["retrieval"]["top_k"] = max(profile["retrieval"].get("top_k", 10), 15)
        profile.setdefault("reranking", {})
        profile["reranking"]["enabled"] = True

    if large_docs:
        profile.setdefault("chunking", {})
        profile["chunking"]["chunk_size"] = 1024
        profile["chunking"]["chunk_overlap"] = 128
        profile["chunking"]["strategy"] = "recursive"

    if needs_precision:
        profile.setdefault("reranking", {})
        profile["reranking"]["enabled"] = True
        profile.setdefault("llm", {})
        profile["llm"]["temperature"] = 0.0
        profile.setdefault("retrieval", {})
        profile["retrieval"]["top_k"] = profile["retrieval"].get("top_k", 10) + 5

    if frequent_updates:
        profile.setdefault("maintenance", {})
        profile["maintenance"]["incremental_indexing"] = True
        profile["maintenance"]["auto_refresh_interval"] = 3600

    if cite_pages:
        profile.setdefault("metadata", {})
        profile["metadata"]["add_page_numbers"] = True
        profile.setdefault("llm", {})
        profile["llm"]["cite_sources"] = True
        profile["llm"]["citation_format"] = "footnote"

    return profile


def get_profile_description(kb_type: str, profile: dict[str, Any]) -> str:
    """Return a human-friendly description of the generated profile."""
    base_desc = PROFILES[kb_type]["description"]

    optimizations = []
    if profile.get("reranking", {}).get("enabled"):
        optimizations.append("reranking enabled")
    if profile.get("chunking", {}).get("chunk_size", 0) > 800:
        optimizations.append("larger chunks for long documents")
    if profile.get("parsing", {}).get("table_extraction"):
        optimizations.append("table extraction")
    if profile.get("metadata", {}).get("add_page_numbers"):
        optimizations.append("page number citations")

    if optimizations:
        return f"{base_desc} — {', '.join(optimizations)}"
    return base_desc
