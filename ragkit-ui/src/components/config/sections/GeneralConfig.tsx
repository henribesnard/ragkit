import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function GeneralConfig({ config, onChange }: SectionProps) {
  const project = config?.project || {};
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Project name</p>
        <Input
          value={project.name || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, name: event.target.value } })}
        />
      </div>
      <div>
        <p className="text-sm font-semibold">Description</p>
        <Textarea
          rows={4}
          value={project.description || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, description: event.target.value } })}
        />
      </div>
      <div>
        <p className="text-sm font-semibold">Environment</p>
        <Select
          value={project.environment || 'development'}
          onChange={(event) => onChange({ ...config, project: { ...project, environment: event.target.value } })}
        >
          <option value="development">Development</option>
          <option value="staging">Staging</option>
          <option value="production">Production</option>
        </Select>
      </div>
    </div>
  );
}
