import { cn } from '@/utils/cn';

interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

export function ToggleSwitch({ checked, onChange, label }: ToggleSwitchProps) {
  return (
    <label className="flex items-center gap-3 text-sm text-ink">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-6 w-11 rounded-full border transition',
          checked ? 'border-accent bg-accent' : 'border-slate-300 bg-slate-200'
        )}
      >
        <span
          className={cn(
            'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition',
            checked ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
      {label ? <span>{label}</span> : null}
    </label>
  );
}
