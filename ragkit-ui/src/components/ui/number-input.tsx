import { Input } from '@/components/ui/input';
import { useTranslation } from 'react-i18next';

interface NumberInputProps {
  value: number | null;
  onChange: (value: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}

export function NumberInput({ value, onChange, min, max, step, unit }: NumberInputProps) {
  const { t } = useTranslation();
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Input
          type="number"
          value={value ?? ''}
          min={min}
          max={max}
          step={step}
          onChange={(event) => {
            const next = event.target.value;
            if (next === '') {
              onChange(null);
              return;
            }
            onChange(Number(next));
          }}
        />
        {unit ? <span className="text-xs text-muted">{unit}</span> : null}
      </div>
      {(min !== undefined || max !== undefined) && (
        <p className="text-xs text-muted">
          {min !== undefined ? `${t('common.labels.min')} ${min}` : null}
          {min !== undefined && max !== undefined ? ' / ' : null}
          {max !== undefined ? `${t('common.labels.max')} ${max}` : null}
        </p>
      )}
    </div>
  );
}
