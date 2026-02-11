import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '@/components/ui/card';
import { cn } from '@/utils/cn';
import type { ExpertiseLevel } from '@/stores/configStore';

interface ExpertiseLevelSelectorProps {
  value: ExpertiseLevel;
  onChange: (value: ExpertiseLevel) => void;
}

export function ExpertiseLevelSelector({ value, onChange }: ExpertiseLevelSelectorProps) {
  const { t } = useTranslation();

  const levels = useMemo(
    () => [
      {
        value: 'simple' as ExpertiseLevel,
        title: t('settings.expertise.simple.title'),
        description: t('settings.expertise.simple.description'),
      },
      {
        value: 'intermediate' as ExpertiseLevel,
        title: t('settings.expertise.intermediate.title'),
        description: t('settings.expertise.intermediate.description'),
      },
      {
        value: 'expert' as ExpertiseLevel,
        title: t('settings.expertise.expert.title'),
        description: t('settings.expertise.expert.description'),
      },
    ],
    [t]
  );

  return (
    <Card className="space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-muted">{t('settings.expertise.label')}</p>
        <h3 className="mt-2 text-lg font-display">{t('settings.expertise.subtitle')}</h3>
      </div>
      <div className="space-y-3">
        {levels.map((level) => (
          <button
            key={level.value}
            type="button"
            onClick={() => onChange(level.value)}
            className={cn(
              'w-full rounded-2xl border border-white/60 px-4 py-3 text-left transition',
              value === level.value
                ? 'bg-accent text-white shadow-glow'
                : 'bg-white/60 text-ink hover:bg-white'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">{level.title}</span>
              {value === level.value ? (
                <span className="text-xs uppercase tracking-[0.2em]">{t('common.labels.active')}</span>
              ) : null}
            </div>
            <p className={cn('mt-2 text-xs', value === level.value ? 'text-white/80' : 'text-muted')}>
              {level.description}
            </p>
          </button>
        ))}
      </div>
    </Card>
  );
}
