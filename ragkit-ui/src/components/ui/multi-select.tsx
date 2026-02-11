import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/utils/cn';

interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  allowCustom?: boolean;
}

export function MultiSelect({ options, selected, onChange, allowCustom }: MultiSelectProps) {
  const { t } = useTranslation();
  const [customValue, setCustomValue] = useState('');

  const toggleValue = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((item) => item !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  const addCustom = () => {
    const trimmed = customValue.trim();
    if (!trimmed) {
      return;
    }
    if (!selected.includes(trimmed)) {
      onChange([...selected, trimmed]);
    }
    setCustomValue('');
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            type="button"
            key={option.value}
            onClick={() => toggleValue(option.value)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs font-semibold transition',
              selected.includes(option.value)
                ? 'border-accent/40 bg-accent/10 text-accent'
                : 'border-slate-200 bg-white/70 text-slate-600 hover:border-accent/30'
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
      {allowCustom ? (
        <div className="flex flex-wrap items-center gap-2">
          <Input
            value={customValue}
            onChange={(event) => setCustomValue(event.target.value)}
            placeholder={t('common.placeholders.addCustomValue')}
            className="flex-1"
          />
          <Button type="button" variant="outline" size="sm" onClick={addCustom}>
            {t('common.actions.add')}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
