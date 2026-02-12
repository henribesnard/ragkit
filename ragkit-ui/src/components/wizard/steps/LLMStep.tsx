import { useTranslation } from 'react-i18next';
import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { ModelSelect } from '@/components/ui/model-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { LLM_MODELS } from '@/data/models';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function LLMStep({ config, onChange }: WizardStepProps) {
  const { t } = useTranslation();
  const llm = config.llm || {};
  const primary = llm.primary || {};

  const updateLLM = (updates: any) => {
    onChange({ ...config, llm: { ...llm, primary: { ...primary, ...updates } } });
  };

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel label={t('wizard.llm.providerLabel')} help={t('wizard.llm.providerHelp')} />
        <Select
          value={primary.provider || 'openai'}
          onChange={(event) => updateLLM({ provider: event.target.value })}
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
        <FieldLabel label={t('wizard.llm.modelLabel')} help={t('wizard.llm.modelHelp')} />
        <ModelSelect
          provider={primary.provider || 'openai'}
          models={LLM_MODELS}
          value={primary.model || ''}
          onChange={(value) => updateLLM({ model: value })}
        />
      </div>
      {primary.provider !== 'ollama' ? (
        <div>
          <FieldLabel label={t('wizard.llm.apiKeyLabel')} help={t('wizard.llm.apiKeyHelp')} />
          <Input
            type="password"
            placeholder="sk-..."
            value={primary.api_key || ''}
            onChange={(event) => updateLLM({ api_key: event.target.value })}
          />
        </div>
      ) : null}

      <CollapsibleSection title={t('wizard.llm.parametersTitle')}>
        <div>
          <FieldLabel label={t('wizard.llm.temperatureLabel')} help={t('wizard.llm.temperatureHelp')} />
          <SliderInput
            value={primary.params?.temperature ?? 0.7}
            onChange={(value) => updateLLM({ params: { ...primary.params, temperature: value } })}
            min={0}
            max={2}
            step={0.1}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.maxTokensLabel')} help={t('wizard.llm.maxTokensHelp')} />
          <NumberInput
            value={primary.params?.max_tokens ?? null}
            min={1}
            max={128000}
            step={1}
            onChange={(value) => updateLLM({ params: { ...primary.params, max_tokens: value } })}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.topPLabel')} help={t('wizard.llm.topPHelp')} />
          <SliderInput
            value={primary.params?.top_p ?? 1}
            onChange={(value) => updateLLM({ params: { ...primary.params, top_p: value } })}
            min={0}
            max={1}
            step={0.05}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.timeoutLabel')} help={t('wizard.llm.timeoutHelp')} />
          <NumberInput
            value={primary.timeout ?? null}
            min={1}
            max={300}
            step={1}
            unit="s"
            onChange={(value) => updateLLM({ timeout: value })}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.maxRetriesLabel')} help={t('wizard.llm.maxRetriesHelp')} />
          <NumberInput
            value={primary.max_retries ?? null}
            min={0}
            max={10}
            step={1}
            onChange={(value) => updateLLM({ max_retries: value })}
          />
        </div>
      </CollapsibleSection>
    </div>
  );
}
