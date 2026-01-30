import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function AgentsConfigSection({ config, onChange }: SectionProps) {
  const agents = config?.agents || {};
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Agents mode</p>
        <Select
          value={agents.mode || 'default'}
          onChange={(event) => onChange({ ...config, agents: { ...agents, mode: event.target.value } })}
        >
          <option value="default">Default</option>
          <option value="custom">Custom</option>
        </Select>
      </div>
    </div>
  );
}
