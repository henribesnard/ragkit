import { HelpTooltip } from '@/components/ui/help-tooltip';

interface FieldLabelProps {
  label: string;
  help?: string;
}

export function FieldLabel({ label, help }: FieldLabelProps) {
  return (
    <div className="flex items-center text-sm font-semibold text-ink">
      <span>{label}</span>
      {help ? <HelpTooltip text={help} /> : null}
    </div>
  );
}
