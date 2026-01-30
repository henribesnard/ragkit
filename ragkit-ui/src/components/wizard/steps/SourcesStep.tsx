import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function SourcesStep({ config, onChange }: WizardStepProps) {
  const ingestion = config.ingestion || {};
  const sources = ingestion.sources || [{}];
  const source = sources[0] || {};
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Source type</p>
        <Select
          value={source.type || 'local'}
          onChange={(event) =>
            onChange({
              ...config,
              ingestion: {
                ...ingestion,
                sources: [{ ...source, type: event.target.value }],
              },
            })
          }
        >
          <option value="local">Local filesystem</option>
        </Select>
      </div>
      <div>
        <p className="text-sm font-semibold">Path</p>
        <Input
          placeholder="./data/documents"
          value={source.path || ''}
          onChange={(event) =>
            onChange({
              ...config,
              ingestion: {
                ...ingestion,
                sources: [{ ...source, path: event.target.value }],
              },
            })
          }
        />
      </div>
      <div>
        <p className="text-sm font-semibold">Patterns</p>
        <Input
          placeholder="*.pdf, *.md, *.txt"
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
