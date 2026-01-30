import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function LLMConfigStep({ config, onChange }: WizardStepProps) {
  const llm = config.llm || {};
  const primary = llm.primary || {};

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Provider</p>
        <Select
          value={primary.provider || 'openai'}
          onChange={(event) =>
            onChange({
              ...config,
              llm: { ...llm, primary: { ...primary, provider: event.target.value } },
            })
          }
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="ollama">Ollama</option>
        </Select>
      </div>
      <div>
        <p className="text-sm font-semibold">Model</p>
        <Input
          placeholder="gpt-4o-mini"
          value={primary.model || ''}
          onChange={(event) =>
            onChange({
              ...config,
              llm: { ...llm, primary: { ...primary, model: event.target.value } },
            })
          }
        />
      </div>
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
    </div>
  );
}
