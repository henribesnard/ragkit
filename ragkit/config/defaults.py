"""Default configuration helpers for setup mode."""

from __future__ import annotations

from ragkit.config.schema import (
    AgentsConfig,
    AgentsGlobalConfig,
    ChunkingConfig,
    ContextConfig,
    DeduplicationConfig,
    FixedChunkingConfig,
    FusionConfig,
    IngestionConfig,
    LexicalParamsConfig,
    LexicalPreprocessingConfig,
    LexicalRetrievalConfig,
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
            ocr=OCRConfig(enabled=False, engine="tesseract", languages=["eng"]),
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
                "You analyze user queries for a RAG system.\n"
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
