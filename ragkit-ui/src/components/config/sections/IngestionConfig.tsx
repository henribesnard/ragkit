import { Input } from '@/components/ui/input';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function IngestionConfigSection({ config, onChange }: SectionProps) {
  const ingestion = config?.ingestion || {};
  const sources = ingestion.sources || [{}];
  const source = sources[0] || {};

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Source path</p>
        <Input
          value={source.path || ''}
          onChange={(event) =>
            onChange({
              ...config,
              ingestion: { ...ingestion, sources: [{ ...source, path: event.target.value }] },
            })
          }
        />
      </div>
      <div>
        <p className="text-sm font-semibold">Patterns</p>
        <Input
          value={(source.patterns || []).join(', ')}
          onChange={(event) =>
            onChange({
              ...config,
              ingestion: {
                ...ingestion,
                sources: [
                  {
                    ...source,
                    patterns: event.target.value
                      .split(',')
                      .map((item: string) => item.trim())
                      .filter(Boolean),
                  },
                ],
              },
            })
          }
        />
      </div>
    </div>
  );
}
