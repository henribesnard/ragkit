import os
from pathlib import Path

import pytest

from ragkit.config import ConfigLoader


@pytest.mark.e2e
def test_config_templates_load():
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("COHERE_API_KEY", "test-key")
    os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
    os.environ.setdefault("QDRANT_API_KEY", "test-key")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

    loader = ConfigLoader()
    paths = [
        Path("templates/minimal.yaml"),
        Path("templates/hybrid.yaml"),
        Path("templates/full.yaml"),
        Path("ragkit-v1-config.yaml"),
    ]
    for path in paths:
        config = loader.load_with_env(path)
        assert config.version == "1.0"
