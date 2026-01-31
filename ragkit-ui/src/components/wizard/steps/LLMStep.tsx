import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function LLMConfigStep({ config, onChange }: WizardStepProps) {
  const llm = config.llm || {};
  const primary = llm.primary || {};
  const provider = primary.provider || 'openai';
  const modelPlaceholder: Record<string, string> = {
    openai: 'gpt-4o-mini',
    anthropic: 'claude-sonnet-4-20250514',
    deepseek: 'deepseek-chat',
    groq: 'llama-3.1-70b-versatile',
    mistral: 'mistral-large-latest',
    ollama: 'llama3',
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Provider</p>
        <Select
          value={provider}
          onChange={(event) =>
            onChange({
              ...config,
              llm: { ...llm, primary: { ...primary, provider: event.target.value } },
            })
          }
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
        <p className="text-sm font-semibold">Model</p>
        <Input
          placeholder={modelPlaceholder[provider] || 'gpt-4o-mini'}
          value={primary.model || ''}
          onChange={(event) =>
            onChange({
              ...config,
              llm: { ...llm, primary: { ...primary, model: event.target.value } },
            })
          }
        />
      </div>
      {provider !== 'ollama' && (
        <div>
          <p className="text-sm font-semibold">API key</p>
          <Input
            placeholder="sk-..."
            value={primary.api_key || ''}
            onChange={(event) =>
              onChange({
                ...config,
                llm: { ...llm, primary: { ...primary, api_key: event.target.value } },
              })
            }
          />
        </div>
      )}
    </div>
  );
}
