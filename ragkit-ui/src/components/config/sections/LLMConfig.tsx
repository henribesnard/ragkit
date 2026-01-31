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
            label="Provider"
            help="Service qui genere les reponses. OpenAI, Anthropic, DeepSeek, Groq et Mistral necessitent une cle API. Ollama tourne en local."
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
          <FieldLabel label="Model" help="Modele LLM a utiliser pour generer les reponses." />
          <ModelSelect
            provider={model.provider || 'openai'}
            models={LLM_MODELS}
            value={model.model || ''}
            onChange={(value) => updateModel(key, { model: value })}
          />
        </div>
        {model.provider !== 'ollama' ? (
          <div>
            <FieldLabel label="API key" help="Cle d'API pour le provider LLM." />
            <Input
              type="password"
              placeholder="sk-..."
              value={model.api_key || ''}
              onChange={(event) => updateModel(key, { api_key: event.target.value })}
            />
          </div>
        ) : null}

        <CollapsibleSection title="Model parameters">
          <div>
            <FieldLabel label="Temperature" help="Controle la creativite. 0 = deterministe, 1+ = creatif." />
            <SliderInput
              value={model.params?.temperature ?? 0.7}
              onChange={(value) => updateModel(key, { params: { ...model.params, temperature: value } })}
              min={0}
              max={2}
              step={0.1}
            />
          </div>
          <div>
            <FieldLabel label="Max tokens" help="Limite maximale de tokens pour la reponse." />
            <NumberInput
              value={model.params?.max_tokens ?? null}
              min={1}
              max={128000}
              step={1}
              onChange={(value) => updateModel(key, { params: { ...model.params, max_tokens: value } })}
            />
          </div>
          <div>
            <FieldLabel label="Top P" help="Echantillonnage nucleus. 1.0 = pas de limite." />
            <SliderInput
              value={model.params?.top_p ?? 1}
              onChange={(value) => updateModel(key, { params: { ...model.params, top_p: value } })}
              min={0}
              max={1}
              step={0.05}
            />
          </div>
          <div>
            <FieldLabel label="Timeout" help="Temps maximum d'attente avant timeout (secondes)." />
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
            <FieldLabel label="Max retries" help="Nombre de tentatives en cas d'erreur." />
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
        <h3 className="text-sm font-semibold text-ink">LLM Principal (Primary)</h3>
        {renderModelFields('primary')}
      </div>

      <CollapsibleSection title="LLM Secondaire">
        <div className="space-y-4">
          <FieldLabel label="Enabled" help="Active un LLM secondaire pour certaines taches." />
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

      <CollapsibleSection title="LLM Rapide">
        <div className="space-y-4">
          <FieldLabel label="Enabled" help="Active un LLM rapide pour les taches simples." />
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
