interface Step {
  id: string;
  title: string;
  description: string;
}

interface WizardProgressProps {
  steps: Step[];
  currentStep: number;
}

export function WizardProgress({ steps, currentStep }: WizardProgressProps) {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => {
        const active = index === currentStep;
        const done = index < currentStep;
        return (
          <div key={step.id} className="flex items-start gap-3">
            <div
              className={`h-8 w-8 rounded-full border text-xs font-semibold flex items-center justify-center ${
                done
                  ? 'border-accent bg-accent text-white'
                  : active
                  ? 'border-accent text-accent'
                  : 'border-slate-200 text-muted'
              }`}
            >
              {index + 1}
            </div>
            <div>
              <p className="text-sm font-semibold">{step.title}</p>
              <p className="text-xs text-muted">{step.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
