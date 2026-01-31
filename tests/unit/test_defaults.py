from ragkit.config.defaults import (
    default_agents_config,
    default_ingestion_config,
    default_retrieval_config,
)
from ragkit.config.schema import (
    EmbeddingConfig,
    EmbeddingModelConfig,
    EmbeddingParams,
    LLMConfig,
    LLMModelConfig,
    LLMParams,
    ProjectConfig,
    RAGKitConfig,
)
from ragkit.config.validators import validate_config


def test_default_ingestion_config():
    config = default_ingestion_config()
    assert config.sources
    assert config.chunking.strategy == "fixed"


def test_default_retrieval_config():
    config = default_retrieval_config()
    assert config.architecture == "semantic"
    assert config.semantic.enabled is True


def test_default_agents_config():
    config = default_agents_config()
    assert config.query_analyzer.llm == "fast"
    assert config.response_generator.llm == "primary"


def test_defaults_pass_validation():
    embedding_model = EmbeddingModelConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key="test",
        params=EmbeddingParams(),
    )
    llm_primary = LLMModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        api_key="test",
        params=LLMParams(),
    )
    config = RAGKitConfig(
        version="1.0",
        project=ProjectConfig(name="test"),
        ingestion=default_ingestion_config(),
        retrieval=default_retrieval_config(),
        agents=default_agents_config(),
        embedding=EmbeddingConfig(document_model=embedding_model, query_model=embedding_model),
        llm=LLMConfig(primary=llm_primary),
    )
    errors = validate_config(config)
    assert errors == []
