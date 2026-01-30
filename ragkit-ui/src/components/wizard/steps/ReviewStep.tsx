interface WizardStepProps {
  config: Record<string, any>;
}

export function ReviewStep({ config }: WizardStepProps) {
  return (
    <div>
      <p className="text-sm font-semibold">Review configuration</p>
      <div className="mt-4 max-h-96 overflow-auto rounded-2xl bg-canvas p-4 text-xs">
        <pre>{JSON.stringify(config, null, 2)}</pre>
      </div>
    </div>
  );
}
