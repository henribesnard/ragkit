export const EMBEDDING_MODELS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: 'text-embedding-3-large', label: 'text-embedding-3-large (3072d, best quality)' },
    { value: 'text-embedding-3-small', label: 'text-embedding-3-small (1536d, fast)' },
    { value: 'text-embedding-ada-002', label: 'text-embedding-ada-002 (1536d, legacy)' },
  ],
  ollama: [
    { value: 'nomic-embed-text', label: 'nomic-embed-text (768d)' },
    { value: 'mxbai-embed-large', label: 'mxbai-embed-large (1024d)' },
    { value: 'all-minilm', label: 'all-minilm (384d, fast)' },
    { value: 'snowflake-arctic-embed', label: 'snowflake-arctic-embed (1024d)' },
  ],
  cohere: [
    { value: 'embed-multilingual-v3.0', label: 'embed-multilingual-v3.0 (1024d, multilingual)' },
    { value: 'embed-english-v3.0', label: 'embed-english-v3.0 (1024d, English)' },
    { value: 'embed-multilingual-light-v3.0', label: 'embed-multilingual-light-v3.0 (384d, fast)' },
  ],
  litellm: [
    { value: 'mistral/mistral-embed', label: 'Mistral Embed (1024d)' },
  ],
};

export const LLM_MODELS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o (flagship, multimodal)' },
    { value: 'gpt-4o-mini', label: 'GPT-4o mini (fast, low cost)' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo (128k context)' },
    { value: 'o1', label: 'o1 (reasoning)' },
    { value: 'o1-mini', label: 'o1-mini (reasoning, fast)' },
  ],
  anthropic: [
    { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (balanced)' },
    { value: 'claude-opus-4-20250514', label: 'Claude Opus 4 (most capable)' },
    { value: 'claude-haiku-3-5-20241022', label: 'Claude 3.5 Haiku (fast, low cost)' },
  ],
  deepseek: [
    { value: 'deepseek-chat', label: 'DeepSeek Chat (V3, general)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner (R1, reasoning)' },
  ],
  groq: [
    { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B (versatile)' },
    { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B (ultra-fast)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B (32k context)' },
    { value: 'gemma2-9b-it', label: 'Gemma 2 9B' },
  ],
  mistral: [
    { value: 'mistral-large-latest', label: 'Mistral Large (best quality)' },
    { value: 'mistral-medium-latest', label: 'Mistral Medium (balanced)' },
    { value: 'mistral-small-latest', label: 'Mistral Small (fast)' },
    { value: 'codestral-latest', label: 'Codestral (code)' },
  ],
  ollama: [
    { value: 'llama3', label: 'Llama 3 8B' },
    { value: 'llama3:70b', label: 'Llama 3 70B' },
    { value: 'mistral', label: 'Mistral 7B' },
    { value: 'mixtral', label: 'Mixtral 8x7B' },
    { value: 'phi3', label: 'Phi-3' },
    { value: 'qwen2', label: 'Qwen 2' },
    { value: 'gemma2', label: 'Gemma 2' },
    { value: 'deepseek-r1', label: 'DeepSeek R1' },
  ],
};
