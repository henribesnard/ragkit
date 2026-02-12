import { useTranslation } from 'react-i18next';
import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { ModelSelect } from '@/components/ui/model-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';
import { LLM_MODELS } from '@/data/models';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function LLMConfigSection({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const llm = config?.llm || {};
  const primary = llm.primary || {};

  const updateLLM = (nextLLM: any) => {
    onChange({ ...config, llm: nextLLM });
  };

  const updateModel = (key: 'primary' | 'secondary' | 'fast', updates: any) => {
    const current = llm[key] || {};
    updateLLM({
      ...llm,
      [key]: { ...current, ...updates },
    });
  };

  const renderModelFields = (key: 'primary' | 'secondary' | 'fast') => {
    const model = llm[key] || {};
    return (
      <div className="space-y-4">
        <div>
          <FieldLabel
            label={t('wizard.llm.providerLabel')}
            help={t('config.llm.providerHelp')}
          />
          <Select
            value={model.provider || 'openai'}
            onChange={(event) => updateModel(key, { provider: event.target.value })}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="deepseek">DeepSeek</option>
            <option value="groq">Groq</option>
            <option value="mistral">Mistral</option>
            <option value="ollama">Ollama</option>
          </Select>
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.modelLabel')} help={t('config.llm.modelHelp')} />
          <ModelSelect
            provider={model.provider || 'openai'}
            models={LLM_MODELS}
            value={model.model || ''}
            onChange={(value) => updateModel(key, { model: value })}
          />
        </div>
        {model.provider !== 'ollama' ? (
          <div>
            <FieldLabel label={t('wizard.llm.apiKeyLabel')} help={t('config.llm.apiKeyHelp')} />
            <Input
              type="password"
              placeholder="sk-..."
              value={model.api_key || ''}
              onChange={(event) => updateModel(key, { api_key: event.target.value })}
            />
          </div>
        ) : null}

        <CollapsibleSection title={t('config.llm.parametersTitle')}>
          <div>
            <FieldLabel label={t('wizard.llm.temperatureLabel')} help={t('config.llm.temperatureHelp')} />
            <SliderInput
              value={model.params?.temperature ?? 0.7}
              onChange={(value) => updateModel(key, { params: { ...model.params, temperature: value } })}
              min={0}
              max={2}
              step={0.1}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.llm.maxTokensLabel')} help={t('config.llm.maxTokensHelp')} />
            <NumberInput
              value={model.params?.max_tokens ?? null}
              min={1}
              max={128000}
              step={1}
              onChange={(value) => updateModel(key, { params: { ...model.params, max_tokens: value } })}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.llm.topPLabel')} help={t('config.llm.topPHelp')} />
            <SliderInput
              value={model.params?.top_p ?? 1}
              onChange={(value) => updateModel(key, { params: { ...model.params, top_p: value } })}
              min={0}
              max={1}
              step={0.05}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.llm.timeoutLabel')} help={t('config.llm.timeoutHelp')} />
            <NumberInput
              value={model.timeout ?? null}
              min={1}
              max={300}
              step={1}
              unit="s"
              onChange={(value) => updateModel(key, { timeout: value })}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.llm.maxRetriesLabel')} help={t('wizard.llm.maxRetriesHelp')} />
            <NumberInput
              value={model.max_retries ?? null}
              min={0}
              max={10}
              step={1}
              onChange={(value) => updateModel(key, { max_retries: value })}
            />
          </div>
        </CollapsibleSection>
      </div>
    );
  };

  const hasSecondary = Boolean(llm.secondary);
  const hasFast = Boolean(llm.fast);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">{t('config.llm.primaryTitle')}</h3>
        {renderModelFields('primary')}
      </div>

      <CollapsibleSection title={t('config.llm.secondaryTitle')}>
        <div className="space-y-4">
          <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.llm.secondaryHelp')} />
          <ToggleSwitch
            checked={hasSecondary}
            onChange={(checked) =>
              updateLLM({
                ...llm,
                secondary: checked
                  ? {
                      provider: primary.provider || 'openai',
                      model: primary.model || '',
                      params: {},
                    }
                  : null,
              })
            }
          />
          {hasSecondary ? renderModelFields('secondary') : null}
        </div>
      </CollapsibleSection>

      <CollapsibleSection title={t('config.llm.fastTitle')}>
        <div className="space-y-4">
          <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.llm.fastHelp')} />
          <ToggleSwitch
            checked={hasFast}
            onChange={(checked) =>
              updateLLM({
                ...llm,
                fast: checked
                  ? {
                      provider: primary.provider || 'openai',
                      model: primary.model || '',
                      params: {},
                    }
                  : null,
              })
            }
          />
          {hasFast ? renderModelFields('fast') : null}
        </div>
      </CollapsibleSection>
    </div>
  );
}
