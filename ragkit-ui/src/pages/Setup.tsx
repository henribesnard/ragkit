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
      const fullConfig = {
        version: config.version || '1.0',
        project: config.project || {
          name: 'ragkit-project',
          description: '',
          environment: 'development',
        },
        ...config,
        ingestion: config.ingestion || defaults.ingestion,
        retrieval: config.retrieval || defaults.retrieval,
        agents: config.agents || defaults.agents,
      };
      await applyConfig(fullConfig);
    } catch (err: any) {
      if (err?.code !== 'ERR_NETWORK' && err?.message !== 'Network Error') {
        setIsRestarting(false);
        setError(err?.message || 'Failed to apply configuration.');
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
