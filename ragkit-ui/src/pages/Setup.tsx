import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { ProjectStep } from '@/components/wizard/steps/ProjectStep';
import { SourcesStep } from '@/components/wizard/steps/SourcesStep';
import { EmbeddingStep } from '@/components/wizard/steps/EmbeddingStep';
import { LLMConfigStep } from '@/components/wizard/steps/LLMStep';
import { RetrievalStep } from '@/components/wizard/steps/RetrievalStep';
import { ReviewStep } from '@/components/wizard/steps/ReviewStep';
import { useUpdateConfig } from '@/hooks/useConfig';

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
  const navigate = useNavigate();
  const { mutate, isPending } = useUpdateConfig();

  const renderStep = (step: number) => {
    switch (step) {
      case 0:
        return <ProjectStep config={config} onChange={setConfig} />;
      case 1:
        return <SourcesStep config={config} onChange={setConfig} />;
      case 2:
        return <EmbeddingStep config={config} onChange={setConfig} />;
      case 3:
        return <LLMConfigStep config={config} onChange={setConfig} />;
      case 4:
        return <RetrievalStep config={config} onChange={setConfig} />;
      default:
        return <ReviewStep config={config} />;
    }
  };

  const handleComplete = () => {
    setError(null);
    mutate(
      { config },
      {
        onSuccess: () => {
          navigate('/config');
        },
        onError: (err: Error) => {
          setError(err.message || 'Failed to save configuration.');
        },
      },
    );
  };

  return (
    <div className="space-y-4">
      <WizardContainer
        steps={STEPS}
        currentStep={currentStep}
        onStepChange={setCurrentStep}
        onComplete={handleComplete}
        renderStep={renderStep}
        isSubmitting={isPending}
      />
      {error && (
        <p className="rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">{error}</p>
      )}
    </div>
  );
}
