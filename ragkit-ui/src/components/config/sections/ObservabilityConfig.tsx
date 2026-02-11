import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
        <h3 className="text-sm font-semibold text-ink">{t('config.observability.loggingTitle')}</h3>
        <div>
          <FieldLabel label={t('config.observability.levelLabel')} help={t('config.observability.levelHelp')} />
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
          <FieldLabel label={t('config.observability.formatLabel')} help={t('config.observability.formatHelp')} />
          <Select
            value={logging.format || 'text'}
            onChange={(event) => updateObservability({ ...observability, logging: { ...logging, format: event.target.value } })}
          >
            <option value="text">{t('common.options.text')}</option>
            <option value="json">JSON</option>
          </Select>
        </div>
        <CollapsibleSection title={t('config.observability.fileTitle')}>
          <div>
            <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.observability.fileEnabledHelp')} />
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
                <FieldLabel label={t('wizard.sources.pathLabel')} help={t('config.observability.filePathHelp')} />
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
                <FieldLabel label={t('config.observability.rotationLabel')} help={t('config.observability.rotationHelp')} />
                <Select
                  value={loggingFile.rotation || 'daily'}
                  onChange={(event) =>
                    updateObservability({
                      ...observability,
                      logging: { ...logging, file: { ...loggingFile, rotation: event.target.value } },
                    })
                  }
                >
                  <option value="daily">{t('common.options.daily')}</option>
                  <option value="weekly">{t('common.options.weekly')}</option>
                  <option value="size-based">{t('common.options.sizeBased')}</option>
                </Select>
              </div>
              <div>
                <FieldLabel label={t('config.observability.retentionLabel')} help={t('config.observability.retentionHelp')} />
                <NumberInput
                  value={loggingFile.retention_days ?? null}
                  min={1}
                  max={365}
                  step={1}
                  unit={t('common.units.days')}
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
        <h3 className="text-sm font-semibold text-ink">{t('config.observability.metricsTitle')}</h3>
        <div>
          <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.observability.metricsEnabledHelp')} />
          <ToggleSwitch
            checked={metrics.enabled ?? true}
            onChange={(checked) => updateObservability({ ...observability, metrics: { ...metrics, enabled: checked } })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.observability.trackLabel')} help={t('config.observability.trackHelp')} />
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
