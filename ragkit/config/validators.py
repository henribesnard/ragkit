"""Custom configuration validation."""

from __future__ import annotations

from urllib.parse import urlparse

from ragkit.config.schema import RAGKitConfig


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def validate_config(config: RAGKitConfig) -> list[str]:
    errors: list[str] = []

    # Vector store validation
    if config.vector_store.provider == "qdrant":
        qdrant = config.vector_store.qdrant
        if qdrant.mode == "local" and not qdrant.path:
            errors.append("vector_store.qdrant.path is required for local mode")
        if qdrant.mode == "cloud":
            if not qdrant.url and not qdrant.url_env:
                errors.append("vector_store.qdrant.url or url_env is required for cloud mode")
            elif qdrant.url and not _is_valid_url(qdrant.url):
                errors.append("vector_store.qdrant.url must be a valid URL")
    if config.vector_store.provider == "chroma":
        chroma = config.vector_store.chroma
        if chroma.mode == "persistent" and not chroma.path:
            errors.append("vector_store.chroma.path is required for persistent mode")

    # Retrieval validation
    if config.retrieval.rerank.enabled and config.retrieval.rerank.provider == "none":
        errors.append("retrieval.rerank.provider must be set when rerank is enabled")

    if config.retrieval.semantic.enabled is False and config.retrieval.lexical.enabled is False:
        errors.append("At least one retrieval mode must be enabled")

    if config.retrieval.architecture in {"hybrid", "hybrid_rerank"}:
        if config.retrieval.semantic.weight + config.retrieval.lexical.weight <= 0:
            errors.append("retrieval semantic/lexical weights must sum to > 0 for hybrid")

    # Embedding / LLM key hints (non-fatal, but we flag missing keys for hosted providers)
    if config.embedding.document_model.provider in {"openai", "cohere"}:
        if not config.embedding.document_model.api_key and not config.embedding.document_model.api_key_env:
            errors.append("embedding.document_model.api_key or api_key_env is required")
    if config.embedding.query_model.provider in {"openai", "cohere"}:
        if not config.embedding.query_model.api_key and not config.embedding.query_model.api_key_env:
            errors.append("embedding.query_model.api_key or api_key_env is required")

    if config.llm.primary.provider in {"openai", "anthropic"}:
        if not config.llm.primary.api_key and not config.llm.primary.api_key_env:
            errors.append("llm.primary.api_key or api_key_env is required")

    if config.retrieval.rerank.enabled and config.retrieval.rerank.provider == "cohere":
        if not config.retrieval.rerank.api_key and not config.retrieval.rerank.api_key_env:
            errors.append("retrieval.rerank.api_key or api_key_env is required")

    return errors
