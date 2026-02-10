"""Tests for the wizard profile logic and API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ragkit.config import wizard as wizard_module
from ragkit.config.profiles import get_profile_description, get_profile_for_answers
from ragkit.desktop.wizard_api import router as wizard_router


def _create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(wizard_router, prefix="/api")
    return app


def test_profile_base_configuration():
    profile = get_profile_for_answers(
        kb_type="technical_documentation",
        has_tables=False,
        needs_multi_doc=False,
        large_docs=False,
        needs_precision=False,
        frequent_updates=False,
        cite_pages=False,
    )

    assert profile["chunking"]["strategy"] == "semantic"
    assert profile["chunking"]["chunk_size"] == 512
    assert profile["retrieval"]["alpha"] == 0.3
    assert profile["reranking"]["enabled"] is True


def test_profile_with_large_documents():
    profile = get_profile_for_answers(
        kb_type="technical_documentation",
        has_tables=False,
        needs_multi_doc=False,
        large_docs=True,
        needs_precision=False,
        frequent_updates=False,
        cite_pages=False,
    )

    assert profile["chunking"]["chunk_size"] == 1024
    assert profile["chunking"]["chunk_overlap"] == 128
    assert profile["chunking"]["strategy"] == "recursive"


def test_profile_with_precision():
    profile = get_profile_for_answers(
        kb_type="legal_regulatory",
        has_tables=False,
        needs_multi_doc=False,
        large_docs=False,
        needs_precision=True,
        frequent_updates=False,
        cite_pages=True,
    )

    assert profile["reranking"]["enabled"] is True
    assert profile["llm"]["temperature"] == 0.0
    assert profile["llm"]["cite_sources"] is True
    assert profile["metadata"]["add_page_numbers"] is True


def test_profile_with_frequent_updates():
    profile = get_profile_for_answers(
        kb_type="faq_support",
        has_tables=False,
        needs_multi_doc=False,
        large_docs=False,
        needs_precision=False,
        frequent_updates=True,
        cite_pages=False,
    )

    assert profile["maintenance"]["incremental_indexing"] is True
    assert profile["maintenance"]["auto_refresh_interval"] == 3600


def test_profile_with_tables():
    profile = get_profile_for_answers(
        kb_type="reports_analysis",
        has_tables=True,
        needs_multi_doc=False,
        large_docs=False,
        needs_precision=False,
        frequent_updates=False,
        cite_pages=False,
    )

    assert profile["parsing"]["table_extraction"] is True
    assert profile["parsing"]["table_strategy"] == "vision"


def test_profile_multi_document():
    profile = get_profile_for_answers(
        kb_type="general_knowledge",
        has_tables=False,
        needs_multi_doc=True,
        large_docs=False,
        needs_precision=False,
        frequent_updates=False,
        cite_pages=False,
    )

    assert profile["retrieval"]["top_k"] >= 15
    assert profile["reranking"]["enabled"] is True


def test_profile_invalid_kb_type():
    with pytest.raises(ValueError):
        get_profile_for_answers(
            kb_type="unknown_type",
            has_tables=False,
            needs_multi_doc=False,
            large_docs=False,
            needs_precision=False,
            frequent_updates=False,
            cite_pages=False,
        )


def test_profile_description_includes_optimizations():
    profile = get_profile_for_answers(
        kb_type="legal_regulatory",
        has_tables=False,
        needs_multi_doc=False,
        large_docs=True,
        needs_precision=True,
        frequent_updates=False,
        cite_pages=True,
    )

    description = get_profile_description("legal_regulatory", profile)
    assert "reranking" in description
    assert "chunks" in description or "chunks" in description.lower()


def test_build_profile_name_variants():
    answers = wizard_module.WizardAnswers(
        kb_type="technical_documentation",
        has_tables_diagrams=False,
        needs_multi_document=False,
        large_documents=True,
        needs_precision=False,
        frequent_updates=False,
        cite_page_numbers=False,
    )

    assert "Long Docs" in wizard_module.build_profile_name(answers)

    answers.needs_precision = True
    assert "Max Precision" in wizard_module.build_profile_name(answers)


def test_build_profile_config_roundtrip():
    answers = wizard_module.WizardAnswers(
        kb_type="faq_support",
        has_tables_diagrams=False,
        needs_multi_document=True,
        large_documents=False,
        needs_precision=False,
        frequent_updates=True,
        cite_page_numbers=False,
    )

    profile_config = wizard_module.build_profile_config(answers)
    assert profile_config.knowledge_base_type == "faq_support"
    assert profile_config.needs_multi_document is True
    assert profile_config.recommended_config["retrieval"]["top_k"] >= 15
    assert profile_config.recommended_config["maintenance"]["incremental_indexing"] is True


def test_analyze_answers_summary_fields():
    answers = wizard_module.WizardAnswers(
        kb_type="general_knowledge",
        has_tables_diagrams=False,
        needs_multi_document=False,
        large_documents=False,
        needs_precision=False,
        frequent_updates=False,
        cite_page_numbers=False,
    )

    analysis = wizard_module.analyze_answers(answers)
    assert analysis.profile_name
    assert "chunking" in analysis.config_summary
    assert "retrieval" in analysis.config_summary
    assert "reranking" in analysis.config_summary
    assert "parsing" in analysis.config_summary


def test_format_parsing_summary_ocr_images():
    summary = wizard_module._format_parsing_summary(
        {"table_extraction": True, "ocr_enabled": True, "image_captioning": True}
    )
    assert "tables" in summary
    assert "ocr" in summary
    assert "images" in summary


def test_analyze_profile_endpoint():
    client = TestClient(_create_app())

    response = client.post(
        "/api/wizard/analyze-profile",
        json={
            "kb_type": "technical_documentation",
            "has_tables_diagrams": True,
            "needs_multi_document": True,
            "large_documents": False,
            "needs_precision": True,
            "frequent_updates": False,
            "cite_page_numbers": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "profile_name" in data
    assert "description" in data
    assert "config_summary" in data
    assert "full_config" in data

    config = data["full_config"]
    assert config["parsing"]["table_extraction"] is True
    assert config["retrieval"]["top_k"] >= 15
    assert config["reranking"]["enabled"] is True
    assert config["metadata"]["add_page_numbers"] is True


def test_environment_detection_endpoint():
    client = TestClient(_create_app())

    response = client.get("/api/wizard/environment-detection")

    assert response.status_code == 200
    data = response.json()

    assert "gpu" in data
    assert "detected" in data["gpu"]
    assert "ollama" in data
    assert "installed" in data["ollama"]
    assert "running" in data["ollama"]


def test_analyze_profile_invalid_kb_type():
    client = TestClient(_create_app())

    response = client.post(
        "/api/wizard/analyze-profile",
        json={
            "kb_type": "unknown_type",
            "has_tables_diagrams": False,
            "needs_multi_document": False,
            "large_documents": False,
            "needs_precision": False,
            "frequent_updates": False,
            "cite_page_numbers": False,
        },
    )

    assert response.status_code == 422
