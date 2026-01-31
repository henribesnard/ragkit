import { useMemo, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface ModelSelectProps {
  provider: string;
  models: Record<string, { value: string; label: string }[]>;
  value: string;
  onChange: (value: string) => void;
}

const CUSTOM_VALUE = '__custom__';

export function ModelSelect({ provider, models, value, onChange }: ModelSelectProps) {
  const options = models[provider] || [];
  const isPreset = options.some((option) => option.value === value);
  const [customValue, setCustomValue] = useState(isPreset ? '' : value);

  const selectValue = useMemo(() => {
    if (isPreset) {
      return value;
    }
    if (customValue) {
      return CUSTOM_VALUE;
    }
    return value;
  }, [customValue, isPreset, value]);

  return (
    <div className="space-y-3">
      <Select
        value={selectValue}
        onChange={(event) => {
          const next = event.target.value;
          if (next === CUSTOM_VALUE) {
            if (!customValue) {
              setCustomValue(value);
            }
            return;
          }
          setCustomValue('');
          onChange(next);
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
        <option value={CUSTOM_VALUE}>Custom</option>
      </Select>
      {selectValue === CUSTOM_VALUE ? (
        <Input
          value={customValue}
          placeholder="custom-model-name"
          onChange={(event) => {
            setCustomValue(event.target.value);
            onChange(event.target.value);
          }}
        />
      ) : null}
    </div>
  );
}
