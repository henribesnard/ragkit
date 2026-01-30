from pathlib import Path
import os

import pytest
from pydantic import ValidationError

from ragkit.config import ConfigLoader


def test_load_minimal_config() -> None:
    loader = ConfigLoader()
    config = loader.load(Path("templates/minimal.yaml"))
    assert config.version == "1.0"
    assert config.project.name


def test_load_with_env_resolution() -> None:
    os.environ["TEST_API_KEY"] = "sk-test123"
    loader = ConfigLoader()
    config = loader.load_with_env(Path("tests/fixtures/config_with_env.yaml"))
    assert config.llm.primary.api_key == "sk-test123"
    assert config.embedding.document_model.api_key == "sk-test123"


def test_validation_errors() -> None:
    loader = ConfigLoader()
    with pytest.raises(ValidationError):
        loader.load(Path("tests/fixtures/invalid_config.yaml"))


def test_full_config_schema() -> None:
    loader = ConfigLoader()
    config = loader.load(Path("ragkit-v1-config.yaml"))
    assert config.ingestion is not None
    assert config.embedding is not None
    assert config.vector_store is not None
    assert config.retrieval is not None
    assert config.llm is not None
    assert config.agents is not None
