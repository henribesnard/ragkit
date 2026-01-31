import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { ProjectStep } from '@/components/wizard/steps/ProjectStep';
import { SourcesStep } from '@/components/wizard/steps/SourcesStep';
import { EmbeddingStep } from '@/components/wizard/steps/EmbeddingStep';
import { LLMStep } from '@/components/wizard/steps/LLMStep';
import { RetrievalStep } from '@/components/wizard/steps/RetrievalStep';
import { ReviewStep } from '@/components/wizard/steps/ReviewStep';
import { applyConfig, fetchDefaults, fetchStatus } from '@/api/config';
import { EMBEDDING_MODELS, LLM_MODELS } from '@/data/models';

const EMBEDDING_ENV_DEFAULTS: Record<string, string> = {
  openai: 'OPENAI_API_KEY',
  cohere: 'COHERE_API_KEY',
};

const LLM_ENV_DEFAULTS: Record<string, string> = {
  openai: 'OPENAI_API_KEY',
  anthropic: 'ANTHROPIC_API_KEY',
  deepseek: 'DEEPSEEK_API_KEY',
  groq: 'GROQ_API_KEY',
  mistral: 'MISTRAL_API_KEY',
};

const FALLBACK_EMBEDDING = {
  document_model: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    api_key_env: 'OPENAI_API_KEY',
    params: { batch_size: 100, dimensions: null },
    cache: { enabled: false, backend: 'memory' },
  },
  query_model: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    api_key_env: 'OPENAI_API_KEY',
    params: { batch_size: 100, dimensions: null },
    cache: { enabled: false, backend: 'memory' },
  },
};

const FALLBACK_LLM = {
  primary: {
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key_env: 'OPENAI_API_KEY',
    params: { temperature: 0.7, max_tokens: 1000, top_p: 0.95 },
    timeout: 60,
    max_retries: 3,
  },
  fast: {
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key_env: 'OPENAI_API_KEY',
    params: { temperature: 0.3, max_tokens: 300, top_p: 0.9 },
  },
};

const getDefaultModel = (
  models: Record<string, { value: string; label: string }[]>,
  provider: string,
  fallback: string,
) => models?.[provider]?.[0]?.value || fallback;

const normalizeEmbeddingModel = (base: any, overrides: any = {}) => {
  const provider = overrides.provider ?? base.provider ?? 'openai';
  const model =
    overrides.model ??
    (provider === base.provider ? base.model : undefined) ??
    getDefaultModel(EMBEDDING_MODELS, provider, 'text-embedding-3-small');
  const params = { ...(base.params || {}), ...(overrides.params || {}) };
  const cache = { ...(base.cache || {}), ...(overrides.cache || {}) };
  const api_key =
    overrides.api_key ?? (provider === base.provider ? base.api_key : undefined);
  let api_key_env =
    overrides.api_key_env ?? (provider === base.provider ? base.api_key_env : undefined);

  if (!api_key && !api_key_env && EMBEDDING_ENV_DEFAULTS[provider]) {
    api_key_env = EMBEDDING_ENV_DEFAULTS[provider];
  }

  return { provider, model, api_key, api_key_env, params, cache };
};

const mergeEmbeddingConfig = (base: any, overrides: any = {}) => {
  const documentModel = normalizeEmbeddingModel(
    base.document_model || {},
    overrides.document_model || {},
  );
  const queryModel = normalizeEmbeddingModel(
    base.query_model || {},
    overrides.query_model || {},
  );
  return {
    ...base,
    ...overrides,
    document_model: documentModel,
    query_model: queryModel,
  };
};

const normalizeLLMModel = (base: any, overrides: any = {}) => {
  const provider = overrides.provider ?? base.provider ?? 'openai';
  const model =
    overrides.model ??
    (provider === base.provider ? base.model : undefined) ??
    getDefaultModel(LLM_MODELS, provider, 'gpt-4o-mini');
  const params = { ...(base.params || {}), ...(overrides.params || {}) };
  const api_key =
    overrides.api_key ?? (provider === base.provider ? base.api_key : undefined);
  let api_key_env =
    overrides.api_key_env ?? (provider === base.provider ? base.api_key_env : undefined);

  if (!api_key && !api_key_env && LLM_ENV_DEFAULTS[provider]) {
    api_key_env = LLM_ENV_DEFAULTS[provider];
  }

  return {
    ...base,
    ...overrides,
    provider,
    model,
    api_key,
    api_key_env,
    params,
  };
};

const mergeLLMConfig = (base: any, overrides: any = {}) => {
  const primary = normalizeLLMModel(base.primary || {}, overrides.primary || {});
  const fast = overrides.fast
    ? normalizeLLMModel(base.fast || base.primary || {}, overrides.fast || {})
    : base.fast;
  const secondary = overrides.secondary
    ? normalizeLLMModel(base.secondary || base.primary || {}, overrides.secondary || {})
    : base.secondary;

  return {
    ...base,
    ...overrides,
    primary,
    fast,
    secondary,
  };
};

const STEPS = [
  { id: 'project', title: 'Project Info', description: 'Name and purpose' },
  { id: 'sources', title: 'Document Sources', description: 'Where documents live' },
  { id: 'embedding', title: 'Embeddings', description: 'Vectorize content' },
  { id: 'llm', title: 'LLM', description: 'Answer generation' },
  { id: 'retrieval', title: 'Retrieval', description: 'Search strategy' },
  { id: 'review', title: 'Review', description: 'Confirm and launch' },
];

export function Setup() {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);
  const [isRestarting, setIsRestarting] = useState(false);
  const navigate = useNavigate();

  const waitForServer = async () => {
    const deadline = Date.now() + 60_000;
    while (Date.now() < deadline) {
      try {
        const status = await fetchStatus();
        if (status?.configured && !status?.setup_mode) {
          return true;
        }
      } catch {
        // Ignore while server is restarting.
      }
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    return false;
  };

  const renderStep = (step: number) => {
    switch (step) {
      case 0:
        return <ProjectStep config={config} onChange={setConfig} />;
      case 1:
        return <SourcesStep config={config} onChange={setConfig} />;
      case 2:
        return <EmbeddingStep config={config} onChange={setConfig} />;
      case 3:
        return <LLMStep config={config} onChange={setConfig} />;
      case 4:
        return <RetrievalStep config={config} onChange={setConfig} />;
      default:
        return <ReviewStep config={config} />;
    }
  };

  const handleComplete = async () => {
    setError(null);
    setIsRestarting(true);
    try {
      const defaults = await fetchDefaults();
      const defaultEmbedding = defaults.embedding || FALLBACK_EMBEDDING;
      const defaultLLM = defaults.llm || FALLBACK_LLM;
      const fullConfig = {
        version: config.version || '1.0',
        project: config.project || {
          name: 'ragkit-project',
          description: '',
          environment: 'development',
        },
        ...config,
        ingestion: config.ingestion || defaults.ingestion,
        embedding: mergeEmbeddingConfig(defaultEmbedding, config.embedding),
        retrieval: config.retrieval || defaults.retrieval,
        llm: mergeLLMConfig(defaultLLM, config.llm),
        agents: config.agents || defaults.agents,
      };
      await applyConfig(fullConfig);
    } catch (err: any) {
      if (err?.code !== 'ERR_NETWORK' && err?.message !== 'Network Error') {
        setIsRestarting(false);
        const details = err?.response?.data?.detail?.errors;
        const detailMessage = Array.isArray(details) ? details.join(' | ') : null;
        setError(detailMessage || err?.message || 'Failed to apply configuration.');
        return;
      }
    }

    const ready = await waitForServer();
    setIsRestarting(false);
    if (ready) {
      navigate('/');
    } else {
      setError('Server did not restart in time. Please refresh.');
    }
  };

  return (
    <div className="space-y-4">
      <WizardContainer
        steps={STEPS}
        currentStep={currentStep}
        onStepChange={setCurrentStep}
        onComplete={handleComplete}
        renderStep={renderStep}
        isSubmitting={isRestarting}
      />
      {error && (
        <p className="rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">{error}</p>
      )}
      {isRestarting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="rounded-3xl bg-white p-8 text-center shadow-xl">
            <p className="text-lg font-semibold">Restarting server...</p>
            <p className="mt-2 text-sm text-slate-600">Applying configuration changes.</p>
          </div>
        </div>
      )}
    </div>
  );
}
