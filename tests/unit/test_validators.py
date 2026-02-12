"""Tests for ragkit.config.validators."""

from pathlib import Path

from ragkit.config import ConfigLoader
from ragkit.config.validators import validate_config


def _load_config(name: str = "ragkit-v1-config.yaml"):
    loader = ConfigLoader()
    return loader.load(Path(name))


def test_valid_config_passes():
    config = _load_config()
    errors = validate_config(config)
    # Errors about missing API keys are expected for a local config,
    # but structural errors should not appear
    structural = [e for e in errors if "path is required" in e or "at least one" in e.lower()]
    assert structural == []


def test_qdrant_local_missing_path():
    config = _load_config()
    config.vector_store.provider = "qdrant"
    config.vector_store.qdrant.mode = "local"
    config.vector_store.qdrant.path = None

    errors = validate_config(config)
    assert any("qdrant.path" in e for e in errors)


def test_qdrant_cloud_missing_url():
    config = _load_config()
    config.vector_store.provider = "qdrant"
    config.vector_store.qdrant.mode = "cloud"
    config.vector_store.qdrant.url = None
    config.vector_store.qdrant.url_env = None

    errors = validate_config(config)
    assert any("qdrant.url" in e for e in errors)


def test_qdrant_cloud_invalid_url():
    config = _load_config()
    config.vector_store.provider = "qdrant"
    config.vector_store.qdrant.mode = "cloud"
    config.vector_store.qdrant.url = "not-a-url"
    config.vector_store.qdrant.url_env = None

    errors = validate_config(config)
    assert any("valid URL" in e for e in errors)


def test_chroma_persistent_missing_path():
    config = _load_config()
    config.vector_store.provider = "chroma"
    config.vector_store.chroma.mode = "persistent"
    config.vector_store.chroma.path = None

    errors = validate_config(config)
    assert any("chroma.path" in e for e in errors)


def test_rerank_enabled_with_no_provider():
    config = _load_config()
    config.retrieval.rerank.enabled = True
    config.retrieval.rerank.provider = "none"

    errors = validate_config(config)
    assert any("rerank.provider" in e for e in errors)


def test_both_retrieval_modes_disabled():
    config = _load_config()
    config.retrieval.semantic.enabled = False
    config.retrieval.lexical.enabled = False

    errors = validate_config(config)
    assert any("retrieval mode" in e.lower() for e in errors)


def test_missing_llm_api_key_flagged():
    config = _load_config()
    config.llm.primary.provider = "openai"
    config.llm.primary.api_key = None
    config.llm.primary.api_key_env = None

    errors = validate_config(config)
    assert any("llm.primary.api_key" in e for e in errors)
