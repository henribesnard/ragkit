export interface ProjectConfig {
  name: string;
  description?: string;
  environment: 'development' | 'staging' | 'production';
}

export interface SourceConfig {
  type: 'local';
  path: string;
  patterns: string[];
  recursive: boolean;
}

export interface OCRConfig {
  enabled: boolean;
  engine: 'tesseract' | 'easyocr';
  languages: string[];
}

export interface ParsingConfig {
  engine: 'auto' | 'unstructured' | 'docling' | 'pypdf';
  ocr: OCRConfig;
}

export interface ChunkingConfig {
  strategy: 'fixed' | 'semantic';
  fixed: {
    chunk_size: number;
    chunk_overlap: number;
  };
  semantic: {
    similarity_threshold: number;
    min_chunk_size: number;
    max_chunk_size: number;
  };
}

export interface MetadataConfig {
  extract: string[];
  custom: Record<string, unknown>;
}

export interface IngestionConfig {
  sources: SourceConfig[];
  parsing: ParsingConfig;
  chunking: ChunkingConfig;
  metadata: MetadataConfig;
}

export interface EmbeddingModelConfig {
  provider: 'openai' | 'ollama' | 'cohere' | 'litellm';
  model: string;
  api_key?: string;
  api_key_env?: string;
  params: {
    batch_size?: number | null;
    dimensions?: number | null;
  };
  cache: {
    enabled: boolean;
    backend: 'memory' | 'disk';
  };
}

export interface EmbeddingConfig {
  document_model: EmbeddingModelConfig;
  query_model: EmbeddingModelConfig;
}

export interface LLMModelConfig {
  provider: 'openai' | 'anthropic' | 'ollama' | 'deepseek' | 'groq' | 'mistral';
  model: string;
  api_key?: string;
  api_key_env?: string;
  params: {
    temperature?: number | null;
    max_tokens?: number | null;
    top_p?: number | null;
  };
  timeout?: number | null;
  max_retries?: number | null;
}

export interface LLMConfig {
  primary: LLMModelConfig;
  secondary?: LLMModelConfig | null;
  fast?: LLMModelConfig | null;
}

export interface RetrievalConfig {
  architecture: 'semantic' | 'lexical' | 'hybrid' | 'hybrid_rerank';
  semantic: {
    enabled: boolean;
    weight: number;
    top_k: number;
    similarity_threshold: number;
  };
  lexical: {
    enabled: boolean;
    weight: number;
    top_k: number;
    algorithm: 'bm25' | 'bm25+';
    params: {
      k1: number;
      b: number;
    };
    preprocessing: {
      lowercase: boolean;
      remove_stopwords: boolean;
      stopwords_lang: 'french' | 'english' | 'auto';
      stemming: boolean;
    };
  };
  rerank: {
    enabled: boolean;
    provider: 'cohere' | 'none';
    model?: string | null;
    api_key?: string | null;
    top_n: number;
    candidates: number;
    relevance_threshold: number;
  };
  fusion: {
    method: 'weighted_sum' | 'reciprocal_rank_fusion';
    normalize_scores: boolean;
    rrf_k: number;
  };
  context: {
    max_chunks: number;
    max_tokens: number;
    deduplication: {
      enabled: boolean;
      similarity_threshold: number;
    };
  };
}

export interface VectorStoreConfig {
  provider: 'qdrant' | 'chroma';
  qdrant: {
    mode: 'memory' | 'local' | 'cloud';
    path?: string | null;
    url?: string | null;
    api_key?: string | null;
    collection_name: string;
    distance_metric: 'cosine' | 'euclidean' | 'dot';
  };
  chroma: {
    mode: 'memory' | 'persistent';
    path?: string | null;
    collection_name: string;
  };
}

export interface AgentsConfig {
  mode: 'default' | 'custom';
  query_analyzer: {
    llm: 'primary' | 'secondary' | 'fast';
    system_prompt: string;
    output_schema: Record<string, unknown>;
    behavior: {
      always_retrieve: boolean;
      detect_intents: string[];
      query_rewriting: {
        enabled: boolean;
        num_rewrites: number;
      };
    };
  };
  response_generator: {
    llm: 'primary' | 'secondary' | 'fast';
    system_prompt: string;
    no_retrieval_prompt: string;
    out_of_scope_prompt: string;
    behavior: {
      cite_sources: boolean;
      citation_format: string;
      admit_uncertainty: boolean;
      uncertainty_phrase: string;
      max_response_length?: number | null;
      response_language: string;
    };
  };
  global: {
    timeout: number;
    max_retries: number;
    retry_delay: number;
    verbose: boolean;
  };
}

export interface ConversationConfig {
  memory: {
    enabled: boolean;
    type: 'buffer_window' | 'summary' | 'none';
    window_size: number;
    include_in_prompt: boolean;
  };
  persistence: {
    enabled: boolean;
    backend: 'memory' | 'redis' | 'postgresql';
  };
}

export interface ChatbotConfig {
  enabled: boolean;
  type: 'gradio';
  server: {
    host: string;
    port: number;
    share: boolean;
  };
  ui: {
    title: string;
    description: string;
    theme: 'soft' | 'default' | 'glass';
    placeholder: string;
    examples: string[];
  };
  features: {
    show_sources: boolean;
    show_latency: boolean;
    streaming: boolean;
    allow_feedback: boolean;
    allow_export: boolean;
  };
}

export interface ObservabilityConfig {
  logging: {
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
    format: 'text' | 'json';
    file: {
      enabled: boolean;
      path?: string | null;
      rotation?: string | null;
      retention_days?: number | null;
    };
  };
  metrics: {
    enabled: boolean;
    track: string[];
  };
}

export interface RAGKitConfig {
  version: string;
  project: ProjectConfig;
  ingestion?: IngestionConfig | null;
  embedding?: EmbeddingConfig | null;
  vector_store: VectorStoreConfig;
  retrieval?: RetrievalConfig | null;
  llm?: LLMConfig | null;
  agents?: AgentsConfig | null;
  conversation?: ConversationConfig;
  chatbot?: ChatbotConfig;
  observability?: ObservabilityConfig;
  [key: string]: unknown;
}
