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

export interface EmbeddingModelConfig {
  provider: 'openai' | 'ollama' | 'cohere';
  model: string;
  api_key?: string;
  api_key_env?: string;
  params: {
    batch_size?: number;
    dimensions?: number;
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
  provider: 'openai' | 'anthropic' | 'ollama';
  model: string;
  api_key?: string;
  api_key_env?: string;
  params: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
  };
  timeout?: number;
  max_retries?: number;
}

export interface LLMConfig {
  primary: LLMModelConfig;
  secondary?: LLMModelConfig;
  fast?: LLMModelConfig;
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
  };
  rerank: {
    enabled: boolean;
    provider: 'cohere' | 'none';
    model?: string;
    top_n: number;
  };
  context: {
    max_chunks: number;
    max_tokens: number;
  };
}

export interface VectorStoreConfig {
  provider: 'qdrant' | 'chroma';
  qdrant: {
    mode: 'memory' | 'local' | 'cloud';
    collection_name: string;
    distance_metric: 'cosine' | 'euclidean' | 'dot';
  };
  chroma: {
    mode: 'memory' | 'persistent';
    collection_name: string;
  };
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

export interface IngestionConfig {
  sources: SourceConfig[];
  parsing: {
    engine: 'auto' | 'unstructured' | 'docling' | 'pypdf';
  };
  chunking: ChunkingConfig;
}

export interface RAGKitConfig {
  version: string;
  project: ProjectConfig;
  ingestion: IngestionConfig;
  embedding: EmbeddingConfig;
  vector_store: VectorStoreConfig;
  retrieval: RetrievalConfig;
  llm: LLMConfig;
  [key: string]: unknown;
}
