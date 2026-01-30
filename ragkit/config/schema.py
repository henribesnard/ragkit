"""Pydantic models for RAGKIT configuration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    environment: Literal["development", "staging", "production"] = "development"


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["local"]
    path: str
    patterns: list[str] = Field(default_factory=list)
    recursive: bool = True


class LocalSourceConfig(SourceConfig):
    model_config = ConfigDict(extra="forbid")



class OCRConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    engine: Literal["tesseract", "easyocr"] = "tesseract"
    languages: list[str] = Field(default_factory=list)


class ParsingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: Literal["auto", "unstructured", "docling", "pypdf"] = "auto"
    ocr: OCRConfig = Field(default_factory=OCRConfig)


class FixedChunkingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_size: int = Field(512, ge=1)
    chunk_overlap: int = Field(50, ge=0)


class SemanticChunkingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)
    min_chunk_size: int = Field(100, ge=1)
    max_chunk_size: int = Field(1000, ge=1)
    embedding_model: str = "document_model"


class ChunkingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Literal["fixed", "semantic"] = "fixed"
    fixed: FixedChunkingConfig = Field(default_factory=FixedChunkingConfig)
    semantic: SemanticChunkingConfig = Field(default_factory=SemanticChunkingConfig)


class MetadataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extract: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class IngestionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: list[SourceConfig]
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)


class EmbeddingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_size: int | None = Field(default=None, ge=1)
    dimensions: int | None = Field(default=None, ge=1)


class EmbeddingCacheConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    backend: Literal["memory", "disk"] = "memory"


class EmbeddingModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["openai", "ollama", "cohere"]
    model: str
    api_key: str | None = None
    api_key_env: str | None = None
    params: EmbeddingParams = Field(default_factory=EmbeddingParams)
    cache: EmbeddingCacheConfig = Field(default_factory=EmbeddingCacheConfig)


class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_model: EmbeddingModelConfig
    query_model: EmbeddingModelConfig


class QdrantConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["memory", "local", "cloud"] = "memory"
    path: str | None = None
    url: str | None = None
    url_env: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    collection_name: str = "ragkit_documents"
    distance_metric: Literal["cosine", "euclidean", "dot"] = "cosine"


class ChromaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["memory", "persistent"] = "memory"
    path: str | None = None
    collection_name: str = "ragkit_documents"


class VectorStoreConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["qdrant", "chroma"] = "qdrant"
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)


class SemanticRetrievalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    weight: float = Field(0.5, ge=0.0, le=1.0)
    top_k: int = Field(20, ge=1)
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0)


class LexicalParamsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k1: float = Field(1.5, ge=0.0)
    b: float = Field(0.75, ge=0.0, le=1.0)


class LexicalPreprocessingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lowercase: bool = True
    remove_stopwords: bool = True
    stopwords_lang: Literal["french", "english", "auto"] = "auto"
    stemming: bool = False


class LexicalRetrievalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    weight: float = Field(0.5, ge=0.0, le=1.0)
    top_k: int = Field(20, ge=1)
    algorithm: Literal["bm25", "bm25+"] = "bm25"
    params: LexicalParamsConfig = Field(default_factory=LexicalParamsConfig)
    preprocessing: LexicalPreprocessingConfig = Field(default_factory=LexicalPreprocessingConfig)


class RerankConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    provider: Literal["cohere", "none"] = "none"
    model: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    top_n: int = Field(5, ge=1)
    candidates: int = Field(40, ge=1)
    relevance_threshold: float = Field(0.0, ge=0.0, le=1.0)


class FusionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["weighted_sum", "reciprocal_rank_fusion"] = "weighted_sum"
    normalize_scores: bool = True
    rrf_k: int = Field(60, ge=1)


class DeduplicationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    similarity_threshold: float = Field(0.95, ge=0.0, le=1.0)


class ContextConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_chunks: int = Field(5, ge=1)
    max_tokens: int = Field(4000, ge=1)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)


class RetrievalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    architecture: Literal["semantic", "lexical", "hybrid", "hybrid_rerank"] = "semantic"
    semantic: SemanticRetrievalConfig = Field(default_factory=SemanticRetrievalConfig)
    lexical: LexicalRetrievalConfig = Field(default_factory=LexicalRetrievalConfig)
    rerank: RerankConfig = Field(default_factory=RerankConfig)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)

    @model_validator(mode="after")
    def _validate_architecture(self) -> "RetrievalConfig":
        if self.architecture in {"lexical", "hybrid", "hybrid_rerank"} and not self.lexical.enabled:
            raise ValueError("lexical.enabled must be true for selected retrieval architecture")
        if self.architecture in {"semantic", "hybrid", "hybrid_rerank"} and not self.semantic.enabled:
            raise ValueError("semantic.enabled must be true for selected retrieval architecture")
        if self.architecture == "hybrid_rerank" and not self.rerank.enabled:
            raise ValueError("rerank.enabled must be true for hybrid_rerank architecture")
        return self


class LLMParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)


class LLMModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: str | None = None
    api_key_env: str | None = None
    params: LLMParams = Field(default_factory=LLMParams)
    timeout: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: LLMModelConfig
    secondary: LLMModelConfig | None = None
    fast: LLMModelConfig | None = None


class QueryRewritingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    num_rewrites: int = Field(1, ge=1, le=3)


class QueryAnalyzerBehaviorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    always_retrieve: bool = False
    detect_intents: list[str] = Field(default_factory=list)
    query_rewriting: QueryRewritingConfig = Field(default_factory=QueryRewritingConfig)


class QueryAnalyzerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: str
    behavior: QueryAnalyzerBehaviorConfig = Field(default_factory=QueryAnalyzerBehaviorConfig)
    system_prompt: str
    output_schema: dict[str, Any] = Field(default_factory=dict)


class ResponseBehaviorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cite_sources: bool = True
    citation_format: str = "[Source: {source_name}]"
    admit_uncertainty: bool = True
    uncertainty_phrase: str = "I could not find relevant information."
    max_response_length: int | None = Field(default=None, ge=1)
    response_language: str = "auto"


class ResponseGeneratorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: str
    behavior: ResponseBehaviorConfig = Field(default_factory=ResponseBehaviorConfig)
    system_prompt: str
    no_retrieval_prompt: str
    out_of_scope_prompt: str


class AgentsGlobalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout: int = Field(30, ge=1)
    max_retries: int = Field(2, ge=0)
    retry_delay: int = Field(1, ge=0)
    verbose: bool = False


class AgentsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode: Literal["default", "custom"] = "default"
    query_analyzer: QueryAnalyzerConfig
    response_generator: ResponseGeneratorConfig
    global_config: AgentsGlobalConfig = Field(default_factory=AgentsGlobalConfig, alias="global")

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str) -> str:
        return value


class ConversationMemoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    type: Literal["buffer_window", "summary", "none"] = "buffer_window"
    window_size: int = Field(10, ge=1)
    include_in_prompt: bool = True


class ConversationPersistenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    backend: Literal["memory", "redis", "postgresql"] = "memory"


class ConversationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory: ConversationMemoryConfig = Field(default_factory=ConversationMemoryConfig)
    persistence: ConversationPersistenceConfig = Field(default_factory=ConversationPersistenceConfig)


class ChatbotServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = Field(8080, ge=1, le=65535)
    share: bool = False


class ChatbotUIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = "RAGKIT Assistant"
    description: str = "Ask questions about your documentation."
    theme: Literal["soft", "default", "glass"] = "soft"
    placeholder: str = "Ask a question..."
    examples: list[str] = Field(default_factory=list)


class ChatbotFeaturesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    show_sources: bool = True
    show_latency: bool = True
    streaming: bool = False
    allow_feedback: bool = False
    allow_export: bool = False


class ChatbotConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    type: Literal["gradio"] = "gradio"
    server: ChatbotServerConfig = Field(default_factory=ChatbotServerConfig)
    ui: ChatbotUIConfig = Field(default_factory=ChatbotUIConfig)
    features: ChatbotFeaturesConfig = Field(default_factory=ChatbotFeaturesConfig)


class APIServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1, le=65535)


class APICorsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    origins: list[str] = Field(default_factory=list)


class APIDocsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    path: str = "/docs"


class APIStreamingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    type: Literal["sse"] = "sse"


class APIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    server: APIServerConfig = Field(default_factory=APIServerConfig)
    cors: APICorsConfig = Field(default_factory=APICorsConfig)
    docs: APIDocsConfig = Field(default_factory=APIDocsConfig)
    streaming: APIStreamingConfig = Field(default_factory=APIStreamingConfig)


class LoggingFileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    path: str | None = None
    rotation: str | None = None
    retention_days: int | None = Field(default=None, ge=1)


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["text", "json"] = "text"
    file: LoggingFileConfig = Field(default_factory=LoggingFileConfig)


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    track: list[str] = Field(default_factory=list)


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)


class RAGKitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    project: ProjectConfig
    ingestion: IngestionConfig
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig
    retrieval: RetrievalConfig
    llm: LLMConfig
    agents: AgentsConfig
    conversation: ConversationConfig
    chatbot: ChatbotConfig
    api: APIConfig
    observability: ObservabilityConfig
