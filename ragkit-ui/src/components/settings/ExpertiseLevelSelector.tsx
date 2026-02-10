import { Card } from '@/components/ui/card';
import { cn } from '@/utils/cn';
import type { ExpertiseLevel } from '@/stores/configStore';

const LEVELS: Array<{
  value: ExpertiseLevel;
  title: string;
  description: string;
}> = [
  {
    value: 'simple',
    title: 'Simple',
    description: 'Profiles pre-configured to get started fast.',
  },
  {
    value: 'intermediate',
    title: 'Intermediate',
    description: 'Tune the core knobs without drowning in details.',
  },
  {
    value: 'expert',
    title: 'Expert',
    description: 'Full JSON control and advanced configuration.',
  },
];

interface ExpertiseLevelSelectorProps {
  value: ExpertiseLevel;
  onChange: (value: ExpertiseLevel) => void;
}

export function ExpertiseLevelSelector({ value, onChange }: ExpertiseLevelSelectorProps) {
  return (
    <Card className="space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-muted">Expertise</p>
        <h3 className="mt-2 text-lg font-display">Choose your cockpit</h3>
      </div>
      <div className="space-y-3">
        {LEVELS.map((level) => (
          <button
            key={level.value}
            type="button"
            onClick={() => onChange(level.value)}
            className={cn(
              'w-full rounded-2xl border border-white/60 px-4 py-3 text-left transition',
              value === level.value
                ? 'bg-accent text-white shadow-glow'
                : 'bg-white/60 text-ink hover:bg-white',
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">{level.title}</span>
              {value === level.value ? (
                <span className="text-xs uppercase tracking-[0.2em]">Active</span>
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
