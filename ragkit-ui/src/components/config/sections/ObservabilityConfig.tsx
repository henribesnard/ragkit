import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { MultiSelect } from '@/components/ui/multi-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

const metricOptions = [
  { value: 'query_count', label: 'query_count' },
  { value: 'query_latency_ms', label: 'query_latency_ms' },
  { value: 'component_latency_ms', label: 'component_latency_ms' },
  { value: 'component_error', label: 'component_error' },
  { value: 'ingestion_runs', label: 'ingestion_runs' },
  { value: 'ingestion_duration_seconds', label: 'ingestion_duration_seconds' },
  { value: 'ingestion_documents', label: 'ingestion_documents' },
  { value: 'ingestion_chunks', label: 'ingestion_chunks' },
  { value: 'ingestion_errors', label: 'ingestion_errors' },
];

export function ObservabilityConfigSection({ config, onChange }: SectionProps) {
  const observability = config?.observability || {};
  const logging = observability.logging || {};
  const loggingFile = logging.file || {};
  const metrics = observability.metrics || {};

  const updateObservability = (nextObservability: any) => {
    onChange({ ...config, observability: nextObservability });
  };

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">Logging</h3>
        <div>
          <FieldLabel label="Level" help="Niveau de logs." />
          <Select
            value={logging.level || 'INFO'}
            onChange={(event) => updateObservability({ ...observability, logging: { ...logging, level: event.target.value } })}
          >
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </Select>
        </div>
        <div>
          <FieldLabel label="Format" help="Format des logs." />
          <Select
            value={logging.format || 'text'}
            onChange={(event) => updateObservability({ ...observability, logging: { ...logging, format: event.target.value } })}
          >
            <option value="text">Text</option>
            <option value="json">JSON</option>
          </Select>
        </div>
        <CollapsibleSection title="File output">
          <div>
            <FieldLabel label="Enabled" help="Ecrire les logs dans un fichier." />
            <ToggleSwitch
              checked={loggingFile.enabled ?? false}
              onChange={(checked) =>
                updateObservability({
                  ...observability,
                  logging: { ...logging, file: { ...loggingFile, enabled: checked } },
                })
              }
            />
          </div>
          {loggingFile.enabled ? (
            <>
              <div>
                <FieldLabel label="Path" help="Chemin du fichier de logs." />
                <Input
                  value={loggingFile.path || ''}
                  onChange={(event) =>
                    updateObservability({
                      ...observability,
                      logging: { ...logging, file: { ...loggingFile, path: event.target.value } },
                    })
                  }
                />
              </div>
              <div>
                <FieldLabel label="Rotation" help="Rotation des logs (daily, weekly, size-based)." />
                <Select
                  value={loggingFile.rotation || 'daily'}
                  onChange={(event) =>
                    updateObservability({
                      ...observability,
                      logging: { ...logging, file: { ...loggingFile, rotation: event.target.value } },
                    })
                  }
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="size-based">Size-based</option>
                </Select>
              </div>
              <div>
                <FieldLabel label="Retention" help="Nombre de jours de retention des logs." />
                <NumberInput
                  value={loggingFile.retention_days ?? null}
                  min={1}
                  max={365}
                  step={1}
                  unit="days"
                  onChange={(value) =>
                    updateObservability({
                      ...observability,
                      logging: { ...logging, file: { ...loggingFile, retention_days: value } },
                    })
                  }
                />
              </div>
            </>
          ) : null}
        </CollapsibleSection>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">Metrics</h3>
        <div>
          <FieldLabel label="Enabled" help="Active la collecte de metriques." />
          <ToggleSwitch
            checked={metrics.enabled ?? true}
            onChange={(checked) => updateObservability({ ...observability, metrics: { ...metrics, enabled: checked } })}
          />
        </div>
        <div>
          <FieldLabel label="Track" help="Metriques a collecter." />
          <MultiSelect
            options={metricOptions}
            selected={metrics.track || []}
            onChange={(selected) => updateObservability({ ...observability, metrics: { ...metrics, track: selected } })}
            allowCustom
          />
        </div>
      </div>
    </div>
  );
}
