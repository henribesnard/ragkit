import { useTranslation } from 'react-i18next';
import { FieldLabel } from '@/components/ui/field-label';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface IntermediateSettingsProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

const setNestedValue = (base: Record<string, any>, path: string[], value: any) => {
  let cursor = base;
  path.forEach((segment, index) => {
    if (index === path.length - 1) {
      cursor[segment] = value;
    } else {
      cursor[segment] = cursor[segment] ?? {};
      cursor = cursor[segment];
    }
  });
};

export function IntermediateSettings({ config, onChange }: IntermediateSettingsProps) {
  const { t } = useTranslation();
  const ingestion = config?.ingestion ?? {};
  const chunking = ingestion.chunking ?? {};
  const fixed = chunking.fixed ?? {};
  const retrieval = config?.retrieval ?? {};
  const semantic = retrieval.semantic ?? {};
  const lexical = retrieval.lexical ?? {};
  const llmPrimary = config?.llm?.primary ?? {};
  const llmParams = llmPrimary.params ?? {};
  const behavior = config?.agents?.response_generator?.behavior ?? {};

  const alpha = semantic.weight ?? 0.5;
  const topK = semantic.top_k ?? lexical.top_k ?? 10;

  const updateConfig = (path: string[], value: any) => {
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, path, value);
    onChange(next);
  };

  const updateAlpha = (nextAlpha: number) => {
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, ['retrieval', 'semantic', 'weight'], nextAlpha);
    setNestedValue(next, ['retrieval', 'lexical', 'weight'], 1 - nextAlpha);
    setNestedValue(next, ['retrieval', 'semantic', 'enabled'], true);
    setNestedValue(next, ['retrieval', 'lexical', 'enabled'], true);
    setNestedValue(next, ['retrieval', 'architecture'], 'hybrid');
    onChange(next);
  };

  const updateTopK = (value: number | null) => {
    const nextValue = value ?? 10;
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, ['retrieval', 'semantic', 'top_k'], nextValue);
    setNestedValue(next, ['retrieval', 'lexical', 'top_k'], nextValue);
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">{t('settings.intermediate.chunkingTitle')}</p>
          <h4 className="mt-2 text-lg font-display">{t('settings.intermediate.chunkingSubtitle')}</h4>
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.strategyLabel')} help={t('settings.intermediate.strategyHelp')} />
          <Select
            value={chunking.strategy || 'fixed'}
            onChange={(event) => updateConfig(['ingestion', 'chunking', 'strategy'], event.target.value)}
          >
            <option value="fixed">{t('common.chunking.fixed')}</option>
            <option value="semantic">{t('common.chunking.semantic')}</option>
          </Select>
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.chunkSizeLabel')} help={t('settings.intermediate.chunkSizeHelp')} />
          <NumberInput
            value={fixed.chunk_size ?? 512}
            min={64}
            max={4096}
            step={64}
            onChange={(value) => updateConfig(['ingestion', 'chunking', 'fixed', 'chunk_size'], value ?? 512)}
          />
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.chunkOverlapLabel')} help={t('settings.intermediate.chunkOverlapHelp')} />
          <NumberInput
            value={fixed.chunk_overlap ?? 50}
            min={0}
            max={512}
            step={10}
            onChange={(value) => updateConfig(['ingestion', 'chunking', 'fixed', 'chunk_overlap'], value ?? 50)}
          />
        </div>
      </section>

      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">{t('settings.intermediate.retrievalTitle')}</p>
          <h4 className="mt-2 text-lg font-display">{t('settings.intermediate.retrievalSubtitle')}</h4>
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.architectureLabel')} help={t('settings.intermediate.architectureHelp')} />
          <Select
            value={retrieval.architecture || 'semantic'}
            onChange={(event) => updateConfig(['retrieval', 'architecture'], event.target.value)}
          >
            <option value="semantic">{t('common.retrieval.semantic')}</option>
            <option value="lexical">{t('common.retrieval.lexical')}</option>
            <option value="hybrid">{t('common.retrieval.hybrid')}</option>
            <option value="hybrid_rerank">{t('common.retrieval.hybridRerank')}</option>
          </Select>
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.topKLabel')} help={t('settings.intermediate.topKHelp')} />
          <NumberInput value={topK} min={1} max={50} step={1} onChange={updateTopK} />
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.balanceLabel')} help={t('settings.intermediate.balanceHelp')} />
          <SliderInput value={alpha} min={0} max={1} step={0.05} onChange={updateAlpha} />
        </div>
      </section>

      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">{t('settings.intermediate.generationTitle')}</p>
          <h4 className="mt-2 text-lg font-display">{t('settings.intermediate.generationSubtitle')}</h4>
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.temperatureLabel')} help={t('settings.intermediate.temperatureHelp')} />
          <SliderInput
            value={llmParams.temperature ?? 0.7}
            min={0}
            max={2}
            step={0.1}
            onChange={(value) => updateConfig(['llm', 'primary', 'params', 'temperature'], value)}
          />
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.maxTokensLabel')} help={t('settings.intermediate.maxTokensHelp')} />
          <NumberInput
            value={llmParams.max_tokens ?? null}
            min={100}
            max={8000}
            step={100}
            onChange={(value) => updateConfig(['llm', 'primary', 'params', 'max_tokens'], value)}
          />
        </div>
        <div>
          <FieldLabel label={t('settings.intermediate.citationsLabel')} help={t('settings.intermediate.citationsHelp')} />
          <ToggleSwitch
            checked={behavior.cite_sources ?? true}
            onChange={(checked) =>
              updateConfig(['agents', 'response_generator', 'behavior', 'cite_sources'], checked)
            }
          />
        </div>
      </section>
    </div>
  );
}
