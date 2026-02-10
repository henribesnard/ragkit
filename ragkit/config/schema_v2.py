"""Pydantic models for RAGKIT v2 configuration."""

from __future__ import annotations

from typing import Any, Callable, Literal, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


def _model_factory(model: type[T]) -> Callable[[], T]:
    return cast(Callable[[], T], model)


class WizardProfileConfig(BaseModel):
    """Configuration detected by the wizard."""

    model_config = ConfigDict(extra="forbid")

    knowledge_base_type: Literal[
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

    detected_profile_name: str
    recommended_config: dict[str, Any]


class GPUInfo(BaseModel):
    """Information about detected GPU capabilities."""

    model_config = ConfigDict(extra="forbid")

    detected: bool
    name: str | None = None
    vram_total_gb: float | None = None
    vram_free_gb: float | None = None


class OllamaInfo(BaseModel):
    """Information about Ollama installation/runtime."""

    model_config = ConfigDict(extra="forbid")

    installed: bool
    running: bool
    version: str | None = None
    models: list[str] = Field(default_factory=list)


class EnvironmentInfo(BaseModel):
    """Environment information for the wizard."""

    model_config = ConfigDict(extra="forbid")

    gpu: GPUInfo
    ollama: OllamaInfo


class DocumentParsingConfig(BaseModel):
    """Document parsing configuration."""

    model_config = ConfigDict(extra="forbid")

    document_loader_type: Literal[
        "auto",
        "pdf",
        "docx",
        "html",
        "markdown",
        "txt",
        "csv",
        "json",
        "xml",
    ] = "auto"

    ocr_enabled: bool = False
    ocr_language: list[str] = Field(default_factory=lambda: ["fra", "eng"])
    ocr_engine: Literal["tesseract", "easyocr", "doctr"] = "tesseract"
    ocr_dpi: int = 300
    ocr_preprocessing: bool = True
    ocr_confidence_threshold: float = 0.6

    table_extraction_strategy: Literal[
        "none",
        "preserve",
        "markdown",
        "separate",
        "vision",
    ] = "preserve"
    table_detection_threshold: float = 0.8
    table_max_columns: int = 20
    table_max_rows: int = 100

    image_extraction_enabled: bool = False
    image_captioning_enabled: bool = False
    image_captioning_model: str | None = "blip-base"
    max_image_size_mb: float = 5.0
    image_formats: list[str] = Field(default_factory=lambda: ["png", "jpg", "jpeg"])

    header_detection: bool = True
    header_hierarchy_enabled: bool = False
    footer_removal: bool = True
    page_number_removal: bool = True
    preserve_formatting: bool = True

    pdf_extraction_method: Literal[
        "pypdf",
        "pdfplumber",
        "pdfminer",
        "unstructured",
    ] = "pdfplumber"
    extract_hyperlinks: bool = False
    extract_footnotes: bool = False
    extract_annotations: bool = False

    min_text_length: int = 50
    max_text_length: int = 1_000_000
    skip_empty_pages: bool = True


class TextPreprocessingConfig(BaseModel):
    """Text preprocessing configuration."""

    model_config = ConfigDict(extra="forbid")

    lowercase: bool = False
    remove_punctuation: bool = False
    normalize_unicode: Literal["NFC", "NFD", "NFKC", "NFKD", "none"] = "NFC"
    remove_urls: bool = False
    remove_emails: bool = False
    remove_phone_numbers: bool = False

    language_detection: bool = False
    language_detector: Literal["langdetect", "fasttext", "langid"] = "langdetect"
    fallback_language: str = "en"
    min_text_length_for_detection: int = 50

    deduplication_strategy: Literal["none", "exact", "fuzzy", "semantic"] = "none"
    deduplication_threshold: float = 0.95
    deduplication_scope: Literal["document", "chunk", "global"] = "chunk"

    remove_special_characters: bool = False
    normalize_whitespace: bool = True
    remove_extra_newlines: bool = True
    fix_encoding_errors: bool = True
    remove_control_characters: bool = True

    custom_regex_filters: list[str] = Field(default_factory=list)
    custom_replacement_rules: dict[str, str] = Field(default_factory=dict)

    remove_stopwords: bool = False
    stopwords_language: str = "english"
    custom_stopwords: list[str] = Field(default_factory=list)


class ChunkingConfigV2(BaseModel):
    """Chunking configuration with all supported strategies."""

    model_config = ConfigDict(extra="forbid")

    strategy: Literal[
        "fixed_size",
        "sentence_based",
        "paragraph_based",
        "semantic",
        "markdown_header",
        "recursive",
        "parent_child",
        "sliding_window",
    ] = "fixed_size"

    chunk_size: int = Field(512, ge=50, le=4000)
    chunk_overlap: int = Field(50, ge=0, le=1000)
    min_chunk_size: int = Field(50, ge=10)
    max_chunk_size: int = Field(2000, ge=100)

    separators: list[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " ", ""])
    keep_separator: bool = True
    separator_regex: str | None = None

    parent_chunk_size: int = Field(2000, ge=50, le=8000)
    child_chunk_size: int = Field(400, ge=50, le=1000)
    parent_child_overlap: int = Field(100, ge=0, le=500)

    sentence_window_size: int = Field(3, ge=1, le=1000)
    window_stride: int = Field(1, ge=1)

    semantic_similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)
    semantic_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_buffer_size: int = Field(1, ge=0, le=5)

    markdown_headers_to_split_on: list[tuple[str, str]] = Field(
        default_factory=lambda: [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
    )

    add_metadata: bool = True
    add_chunk_index: bool = True
    add_document_title: bool = True
    add_section_title: bool = False
    add_page_number: bool = False
    add_paragraph_index: bool = False

    strip_whitespace: bool = True
    merge_short_chunks: bool = True
    split_long_sentences: bool = False

    tokenizer_name: str = "cl100k_base"


class EmbeddingConfigV2(BaseModel):
    """Embedding configuration with multi-provider support."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal[
        "openai",
        "cohere",
        "huggingface",
        "sentence_transformers",
        "ollama",
        "voyage",
        "onnx_local",
        "google",
    ] = "openai"
    model: str = "text-embedding-3-small"

    dimensions: int | None = Field(default=None, ge=64, le=4096)
    dimensionality_reduction: Literal["none", "pca", "umap"] = "none"
    reduction_target_dims: int | None = Field(default=None, ge=64, le=2048)

    normalize_embeddings: bool = True
    embedding_dtype: Literal["float32", "float16", "int8"] = "float32"

    batch_size: int = Field(32, ge=1, le=2048)
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay: float = Field(1.0, ge=0.0, le=60.0)
    rate_limit_rpm: int | None = Field(default=None, ge=1)
    rate_limit_tpm: int | None = Field(default=None, ge=1)

    max_tokens_per_chunk: int = Field(8192, ge=1, le=100000)
    truncation_strategy: Literal["start", "end", "middle", "split"] = "end"
    pooling_strategy: Literal["mean", "max", "cls", "last"] = "mean"

    api_key: str | None = None
    api_key_env: str | None = None
    api_base_url: str | None = None
    timeout: int = Field(60, ge=1, le=300)

    cache_embeddings: bool = True
    cache_size_mb: int = Field(512, ge=0, le=10240)
    cache_ttl: int = Field(86400, ge=0)

    use_separate_query_model: bool = False
    query_model: str | None = None
    query_instruction_prefix: str | None = None
    document_instruction_prefix: str | None = None

    use_gpu: bool = False
    num_workers: int = Field(1, ge=1, le=32)


class VectorDBConfigV2(BaseModel):
    """Vector database configuration."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal[
        "chromadb",
        "qdrant",
        "pinecone",
        "weaviate",
        "milvus",
        "faiss",
    ] = "chromadb"

    distance_metric: Literal["cosine", "euclidean", "dot_product", "manhattan"] = "cosine"

    index_type: Literal["HNSW", "IVF", "FLAT", "LSH", "IVF_FLAT", "IVF_PQ"] = "HNSW"

    hnsw_m: int = Field(16, ge=4, le=64)
    hnsw_ef_construction: int = Field(200, ge=100, le=1000)
    hnsw_ef_search: int = Field(50, ge=10, le=500)

    ivf_nlist: int | None = Field(default=None, ge=1)
    ivf_nprobe: int = Field(10, ge=1, le=1000)

    quantization_type: Literal["none", "scalar", "product", "binary"] = "none"
    pq_m: int = Field(8, ge=1, le=64)
    pq_nbits: int = Field(8, ge=4, le=16)

    num_shards: int = Field(1, ge=1, le=100)
    num_replicas: int = Field(1, ge=1, le=10)
    replication_factor: int = Field(1, ge=1, le=10)

    metadata_index_fields: list[str] = Field(default_factory=list)
    filter_strategy: Literal["pre_filter", "post_filter"] = "pre_filter"

    batch_size: int = Field(100, ge=1, le=10000)
    max_concurrent_operations: int = Field(10, ge=1, le=100)
    connection_pool_size: int = Field(10, ge=1, le=100)

    storage_path: str | None = None
    in_memory: bool = False
    persist_on_disk: bool = True
    collection_name: str = "ragkit_default"


class RetrievalConfigV2(BaseModel):
    """Retrieval configuration for dense/lexical/hybrid search."""

    model_config = ConfigDict(extra="forbid")

    retrieval_mode: Literal["semantic", "lexical", "hybrid"] = "hybrid"

    query_preprocessing: bool = True
    query_expansion: Literal["none", "synonyms", "llm_rewrite"] = "none"
    multi_query_strategy: Literal["single", "multi_perspective", "hyde"] = "single"

    top_k: int = 10
    score_threshold: float = 0.0

    mmr_enabled: bool = False
    mmr_lambda: float = 0.5
    diversity_threshold: float = 0.8

    filter_conditions: dict[str, Any] = Field(default_factory=dict)
    filter_mode: Literal["must", "should", "must_not"] = "must"

    tokenizer_type: Literal["standard", "whitespace", "ngram"] = "standard"
    lowercase_tokens: bool = True
    remove_stopwords: bool = True
    stopwords_language: str = "english"
    custom_stopwords: list[str] = Field(default_factory=list)

    stemming_enabled: bool = False
    lemmatization_enabled: bool = False

    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    bm25_delta: float = 0.5

    ngram_range: tuple[int, int] = (1, 2)
    max_features: int | None = None

    alpha: float = 0.5
    fusion_method: Literal["rrf", "linear", "weighted_sum", "relative_score"] = "rrf"
    rrf_k: int = 60

    normalize_scores: bool = True
    normalization_method: Literal["min-max", "z-score", "softmax"] = "min-max"

    dynamic_alpha: bool = False
    query_classifier_enabled: bool = False


class RerankingConfigV2(BaseModel):
    """Reranking configuration for cross-encoders."""

    model_config = ConfigDict(extra="forbid")

    reranker_enabled: bool = False
    reranker_model: Literal[
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "cross-encoder/ms-marco-TinyBERT-L-2-v2",
        "BAAI/bge-reranker-v2-m3",
        "cross-encoder/ms-marco-electra-base",
        "cohere-rerank-v3",
        "llm-based",
        "colbert",
    ] = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    rerank_top_n: int = 100
    rerank_batch_size: int = 16
    rerank_threshold: float = 0.0
    final_top_k: int = 5
    return_scores: bool = True

    multi_stage_reranking: bool = False
    stage_1_model: str = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
    stage_2_model: str = "BAAI/bge-reranker-v2-m3"
    stage_1_keep_top: int = 50

    use_gpu: bool = True
    half_precision: bool = False
    cache_model: bool = True


class LLMGenerationConfigV2(BaseModel):
    """LLM generation configuration for RAG."""

    model_config = ConfigDict(extra="forbid")

    model: str = "gpt-4o-mini"
    provider: Literal["openai", "anthropic", "ollama", "azure", "together"] = "openai"

    temperature: float = 0.1
    max_tokens: int = 1000
    top_p: float = 0.9
    top_k: int | None = None

    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    stream: bool = False

    system_prompt: str = (
        "You are a helpful assistant. Answer the question based ONLY on the provided context. "
        "If the context does not contain enough information, say 'I do not have enough information.'"
    )
    few_shot_examples: list[dict[str, Any]] = Field(default_factory=list)
    chain_of_thought: bool = False
    output_format: Literal["text", "json", "markdown"] = "text"
    json_schema: dict[str, Any] | None = None

    max_context_tokens: int = 4000
    context_window_strategy: Literal[
        "truncate_middle",
        "truncate_end",
        "summarize_overflow",
        "sliding_window",
    ] = "truncate_middle"
    context_compression: bool = False
    compression_ratio: float = 0.5
    context_ordering: Literal["relevance", "chronological", "lost_in_middle"] = "lost_in_middle"

    cite_sources: bool = True
    citation_format: Literal["numbered", "footnote", "inline"] = "numbered"
    include_metadata_in_citation: bool = True
    citation_template: str = "[Source: {source_name}, p.{page}]"
    require_citation_for_facts: bool = True

    enable_fallback: bool = True
    fallback_message: str = (
        "Je n'ai pas trouve d'informations pertinentes dans la base de connaissances."
    )
    confidence_threshold: float = 0.5
    content_filters: list[str] = Field(default_factory=lambda: ["toxicity", "pii"])
    max_retries: int = 3
    retry_delay: float = 1.0

    timeout: float = 30.0
    cache_responses: bool = True
    cache_ttl: int = 3600


class CacheConfigV2(BaseModel):
    """Multi-level cache configuration."""

    model_config = ConfigDict(extra="forbid")

    query_cache_enabled: bool = True
    query_cache_ttl: int = 3600
    query_cache_size_mb: int = 512
    cache_key_strategy: Literal["exact", "fuzzy", "semantic"] = "semantic"
    semantic_cache_threshold: float = 0.95

    embedding_cache_enabled: bool = True
    embedding_cache_ttl: int = 86400
    embedding_cache_size_mb: int = 1024

    result_cache_enabled: bool = True
    result_cache_ttl: int = 1800
    result_cache_size_mb: int = 2048

    async_processing: bool = True
    batch_size: int = 32
    batch_timeout_ms: int = 100
    concurrent_requests: int = 10
    queue_max_size: int = 1000

    warmup_enabled: bool = True
    warmup_queries: list[str] = Field(default_factory=list)
    preload_index: bool = False

    compress_cache: bool = True
    compression_algorithm: Literal["gzip", "lz4", "zstd"] = "lz4"

    cache_backend: Literal["memory", "redis", "hybrid"] = "hybrid"
    redis_url: str | None = None


class MonitoringConfigV2(BaseModel):
    """Monitoring and evaluation configuration."""

    model_config = ConfigDict(extra="forbid")

    track_retrieval_metrics: bool = True
    precision_at_k: list[int] = Field(default_factory=lambda: [1, 3, 5, 10])
    recall_at_k: list[int] = Field(default_factory=lambda: [3, 5, 10])
    track_mrr: bool = True
    track_ndcg: bool = True

    track_generation_metrics: bool = True
    faithfulness_enabled: bool = True
    answer_relevancy_enabled: bool = True
    context_precision_enabled: bool = True
    context_recall_enabled: bool = True
    answer_correctness_enabled: bool = False

    track_latency: bool = True
    latency_percentiles: list[int] = Field(default_factory=lambda: [50, 95, 99])
    track_throughput: bool = True
    track_cost: bool = True
    cost_breakdown: bool = True

    log_all_queries: bool = True
    log_sampling_rate: float = 1.0
    metrics_backend: Literal["prometheus", "datadog", "custom"] = "prometheus"
    metrics_retention_days: int = 30

    enable_alerts: bool = True
    alert_latency_p95_threshold_ms: int = 3000
    alert_faithfulness_threshold: float = 0.75
    alert_cost_daily_threshold_usd: float = 100.0


class SecurityConfigV2(BaseModel):
    """Security and compliance configuration."""

    model_config = ConfigDict(extra="forbid")

    pii_detection_enabled: bool = True
    pii_detection_mode: Literal["detect", "redact", "block"] = "redact"
    pii_entities: list[str] = Field(
        default_factory=lambda: [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "SSN",
            "CREDIT_CARD",
            "IBAN",
            "IP_ADDRESS",
        ]
    )
    pii_confidence_threshold: float = 0.8

    content_moderation_enabled: bool = True
    toxicity_threshold: float = 0.7
    block_prompt_injection: bool = True
    block_jailbreak_attempts: bool = True

    access_control_enabled: bool = False
    require_authentication: bool = False
    role_based_access: bool = False

    audit_logging_enabled: bool = True
    log_all_queries: bool = True
    log_document_access: bool = True
    log_retention_days: int = 90

    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_day: int = 1000

    encrypt_cache: bool = True
    encrypt_logs: bool = False


class MaintenanceConfigV2(BaseModel):
    """Maintenance and update configuration."""

    model_config = ConfigDict(extra="forbid")

    incremental_indexing: bool = False
    update_strategy: Literal["append", "upsert", "full_reindex"] = "append"
    document_versioning: bool = False
    index_versioning: bool = False
    auto_refresh_interval: int | None = None
    refresh_strategy: Literal["scheduled", "on_demand", "webhook-triggered"] = "scheduled"


class RAGKitConfigV2(BaseModel):
    """Top-level configuration container for v2."""

    model_config = ConfigDict(extra="forbid")

    wizard: WizardProfileConfig | None = None
    parsing: DocumentParsingConfig = Field(default_factory=_model_factory(DocumentParsingConfig))
    preprocessing: TextPreprocessingConfig = Field(default_factory=_model_factory(TextPreprocessingConfig))
    chunking: ChunkingConfigV2 = Field(default_factory=_model_factory(ChunkingConfigV2))
    embedding: EmbeddingConfigV2 = Field(default_factory=_model_factory(EmbeddingConfigV2))
    vector_db: VectorDBConfigV2 = Field(default_factory=_model_factory(VectorDBConfigV2))
    retrieval: RetrievalConfigV2 = Field(default_factory=_model_factory(RetrievalConfigV2))
    reranking: RerankingConfigV2 = Field(default_factory=_model_factory(RerankingConfigV2))
    llm: LLMGenerationConfigV2 = Field(default_factory=_model_factory(LLMGenerationConfigV2))
    cache: CacheConfigV2 = Field(default_factory=_model_factory(CacheConfigV2))
    monitoring: MonitoringConfigV2 = Field(default_factory=_model_factory(MonitoringConfigV2))
    security: SecurityConfigV2 = Field(default_factory=_model_factory(SecurityConfigV2))
    maintenance: MaintenanceConfigV2 = Field(default_factory=_model_factory(MaintenanceConfigV2))
