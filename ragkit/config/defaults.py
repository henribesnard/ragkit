"""Default configuration helpers for setup mode."""

from __future__ import annotations

from pathlib import Path

from ragkit.config.schema import (
    AgentsConfig,
    AgentsGlobalConfig,
    ChunkingConfig,
    ContextConfig,
    DeduplicationConfig,
    EmbeddingConfig,
    EmbeddingModelConfig,
    EmbeddingParams,
    FixedChunkingConfig,
    FusionConfig,
    IngestionConfig,
    LexicalParamsConfig,
    LexicalPreprocessingConfig,
    LexicalRetrievalConfig,
    LLMConfig,
    LLMModelConfig,
    LLMParams,
    MetadataConfig,
    OCRConfig,
    ParsingConfig,
    QueryAnalyzerBehaviorConfig,
    QueryAnalyzerConfig,
    QueryRewritingConfig,
    RerankConfig,
    ResponseBehaviorConfig,
    ResponseGeneratorConfig,
    RetrievalConfig,
    SemanticChunkingConfig,
    SemanticRetrievalConfig,
    SourceConfig,
)
from ragkit.utils.language import detect_language

_OCR_LANGUAGE_MAP: dict[str, str] = {
    "en": "eng",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
}


def default_ingestion_config() -> IngestionConfig:
    return IngestionConfig(
        sources=[
            SourceConfig(
                type="local",
                path="./data/documents",
                patterns=["*.md", "*.txt"],
                recursive=True,
            )
        ],
        parsing=ParsingConfig(
            engine="auto",
            ocr=OCRConfig(enabled=False, engine="tesseract", languages=_default_ocr_languages()),
        ),
        chunking=ChunkingConfig(
            strategy="fixed",
            fixed=FixedChunkingConfig(chunk_size=512, chunk_overlap=50),
            semantic=SemanticChunkingConfig(
                similarity_threshold=0.85,
                min_chunk_size=100,
                max_chunk_size=1000,
                embedding_model="document_model",
            ),
        ),
        metadata=MetadataConfig(extract=["source_path", "file_type"], custom={}),
    )


def default_embedding_config() -> EmbeddingConfig:
    document_model = EmbeddingModelConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key_env="OPENAI_API_KEY",
        params=EmbeddingParams(batch_size=100, dimensions=None),
    )
    query_model = EmbeddingModelConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key_env="OPENAI_API_KEY",
        params=EmbeddingParams(batch_size=100, dimensions=None),
    )
    return EmbeddingConfig(document_model=document_model, query_model=query_model)


def default_retrieval_config() -> RetrievalConfig:
    return RetrievalConfig(
        architecture="semantic",
        semantic=SemanticRetrievalConfig(
            enabled=True,
            weight=1.0,
            top_k=10,
            similarity_threshold=0.0,
        ),
        lexical=LexicalRetrievalConfig(
            enabled=False,
            weight=0.0,
            top_k=10,
            algorithm="bm25",
            params=LexicalParamsConfig(k1=1.5, b=0.75),
            preprocessing=LexicalPreprocessingConfig(
                lowercase=True,
                remove_stopwords=True,
                stopwords_lang="english",
                stemming=False,
            ),
        ),
        rerank=RerankConfig(
            enabled=False,
            provider="none",
            model=None,
            api_key=None,
            api_key_env=None,
            top_n=5,
            candidates=20,
            relevance_threshold=0.0,
        ),
        fusion=FusionConfig(method="weighted_sum", normalize_scores=True, rrf_k=60),
        context=ContextConfig(
            max_chunks=4,
            max_tokens=2000,
            deduplication=DeduplicationConfig(enabled=True, similarity_threshold=0.95),
        ),
    )


def default_llm_config() -> LLMConfig:
    primary = LLMModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        params=LLMParams(temperature=0.7, max_tokens=1000, top_p=0.95),
        timeout=60,
        max_retries=3,
    )
    fast = LLMModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        params=LLMParams(temperature=0.3, max_tokens=300, top_p=0.9),
    )
    return LLMConfig(primary=primary, fast=fast)


def default_agents_config() -> AgentsConfig:
    payload = {
        "mode": "default",
        "query_analyzer": QueryAnalyzerConfig(
            llm="fast",
            behavior=QueryAnalyzerBehaviorConfig(
                always_retrieve=False,
                detect_intents=[
                    "question",
                    "greeting",
                    "chitchat",
                    "out_of_scope",
                    "clarification",
                ],
                query_rewriting=QueryRewritingConfig(enabled=True, num_rewrites=1),
            ),
            system_prompt=(
                "You analyze user queries for a RAG (Retrieval-Augmented Generation) system.\n"
                "Classify the query intent as one of the allowed values.\n\n"
                "Intent definitions:\n"
                "- question: a question that can be answered using the document knowledge base\n"
                "- greeting: a greeting or hello message\n"
                "- chitchat: casual conversation unrelated to the knowledge base\n"
                "- out_of_scope: a question that clearly cannot be answered from the document "
                "knowledge base (e.g. recipes, sports scores, general knowledge unrelated to "
                "the documents)\n"
                "- clarification: user asks for clarification about a previous answer\n\n"
                "Set needs_retrieval=true only for 'question' and 'clarification'.\n"
                "Set needs_retrieval=false for 'greeting', 'chitchat', and 'out_of_scope'.\n\n"
                "Return JSON with intent, needs_retrieval, rewritten_query, reasoning."
            ),
            output_schema={
                "type": "object",
                "required": ["intent", "needs_retrieval"],
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "question",
                            "greeting",
                            "chitchat",
                            "out_of_scope",
                            "clarification",
                        ],
                    },
                    "needs_retrieval": {"type": "boolean"},
                    "rewritten_query": {"type": ["string", "null"]},
                    "reasoning": {"type": "string"},
                },
            },
        ),
        "response_generator": ResponseGeneratorConfig(
            llm="primary",
            behavior=ResponseBehaviorConfig(
                cite_sources=True,
                citation_format="[Source: {source_name}]",
                admit_uncertainty=True,
                uncertainty_phrase="I could not find relevant information in the documents.",
                max_response_length=None,
                response_language="auto",
                source_path_mode="basename",
            ),
            system_prompt=(
                "You answer using only the provided context.\n"
                "Cite sources using [Source: name].\n"
                "Context:\n"
                "{context}"
            ),
            no_retrieval_prompt="You are a friendly assistant. Answer briefly.",
            out_of_scope_prompt="Politely explain the question is outside the supported scope.",
        ),
        "global": AgentsGlobalConfig(timeout=30, max_retries=2, retry_delay=1, verbose=False),
    }
    return AgentsConfig.model_validate(payload)


def _default_ocr_languages() -> list[str]:
    code = _detect_language_from_docs(Path("./data/documents"))
    if code:
        mapped = _OCR_LANGUAGE_MAP.get(code)
        if mapped:
            return [mapped]
    return ["eng"]


def _detect_language_from_docs(base_path: Path) -> str | None:
    if not base_path.exists():
        return None
    for suffix in (".txt", ".md"):
        for path in base_path.rglob(f"*{suffix}"):
            try:
                sample = path.read_text(encoding="utf-8", errors="ignore")[:2000]
            except Exception:
                continue
            code = detect_language(sample)
            if code:
                return code
    return None
