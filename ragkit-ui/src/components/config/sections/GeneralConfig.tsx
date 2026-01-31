import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { FieldLabel } from '@/components/ui/field-label';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function GeneralConfig({ config, onChange }: SectionProps) {
  const project = config?.project || {};
  return (
    <div className="space-y-6">
      <div>
        <FieldLabel
          label="Project name"
          help="Nom unique de votre projet RAG. Utilise dans les logs et l'interface."
        />
        <Input
          value={project.name || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, name: event.target.value } })}
        />
      </div>
      <div>
        <FieldLabel
          label="Description"
          help="Description libre du projet. Aide a documenter l'objectif du systeme RAG."
        />
        <Textarea
          rows={4}
          value={project.description || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, description: event.target.value } })}
        />
      </div>
      <div>
        <FieldLabel
          label="Environment"
          help="development : logs verbeux, rechargement rapide. staging : test pre-production. production : optimise pour la performance."
        />
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
