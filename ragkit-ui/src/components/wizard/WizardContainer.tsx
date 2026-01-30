import { ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { WizardProgress } from './WizardProgress';

interface Step {
  id: string;
  title: string;
  description: string;
}

interface WizardContainerProps {
  steps: Step[];
  currentStep: number;
  onStepChange: (step: number) => void;
  onComplete: () => void;
  renderStep: (step: number) => ReactNode;
  isSubmitting?: boolean;
}

export function WizardContainer({
  steps,
  currentStep,
  onStepChange,
  onComplete,
  renderStep,
  isSubmitting,
}: WizardContainerProps) {
  const isLast = currentStep === steps.length - 1;

  return (
    <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
      <div className="rounded-3xl bg-white/80 p-6 shadow-soft">
        <WizardProgress steps={steps} currentStep={currentStep} />
      </div>
      <div className="rounded-3xl bg-white/80 p-8 shadow-soft">
        {renderStep(currentStep)}
        <div className="mt-10 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => onStepChange(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Back
          </Button>
          <Button
            onClick={() => (isLast ? onComplete() : onStepChange(currentStep + 1))}
            disabled={isLast && isSubmitting}
          >
            {isLast ? (isSubmitting ? 'Saving...' : 'Launch') : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  );
}
