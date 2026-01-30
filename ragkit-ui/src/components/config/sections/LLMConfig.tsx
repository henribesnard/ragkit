import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function LLMConfigSection({ config, onChange }: SectionProps) {
  const llm = config?.llm || {};
  const primary = llm.primary || {};
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Provider</p>
        <Select
          value={primary.provider || 'openai'}
          onChange={(event) => onChange({ ...config, llm: { ...llm, primary: { ...primary, provider: event.target.value } } })}
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="ollama">Ollama</option>
        </Select>
      </div>
      <div>
        <p className="text-sm font-semibold">Model</p>
        <Input
          value={primary.model || ''}
          onChange={(event) => onChange({ ...config, llm: { ...llm, primary: { ...primary, model: event.target.value } } })}
        />
      </div>
    </div>
  );
}
