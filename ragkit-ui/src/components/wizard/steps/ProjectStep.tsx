
import { useState } from 'react';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { RAG_PROFILES, RagProfile, applyProfilePatch } from '@/data/profiles';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function ProjectStep({ config, onChange }: WizardStepProps) {
  const project = config.project || {};
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);

  const handleProfileSelect = (profile: RagProfile) => {
    setSelectedProfile(profile.id);
    const nextConfig = applyProfilePatch(config, profile);
    onChange(nextConfig);
  };

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel
          label="Project name"
          help="Nom unique de votre projet RAG. Utilise dans les logs et l'interface."
        />
        <Input
          placeholder="Acme Knowledge Base"
          value={project.name || ''}
          onChange={(event) =>
            onChange({
              ...config,
              project: { ...project, name: event.target.value },
            })
          }
        />
      </div>
      <div>
        <FieldLabel
          label="Description"
          help="Description libre du projet. Aide a documenter l'objectif du systeme RAG."
        />
        <Textarea
          placeholder="Explain what this RAG system powers"
          rows={4}
          value={project.description || ''}
          onChange={(event) =>
            onChange({
              ...config,
              project: { ...project, description: event.target.value },
            })
          }
        />
      </div>
      <div>
        <FieldLabel
          label="Environment"
          help="development : logs verbeux, rechargement rapide. staging : test pre-production. production : optimise pour la performance."
        />
        <Select
          value={project.environment || 'development'}
          onChange={(event) =>
            onChange({
              ...config,
              project: { ...project, environment: event.target.value },
            })
          }
        >
          <option value="development">Development</option>
          <option value="staging">Staging</option>
          <option value="production">Production</option>
        </Select>
      </div>

      <div className="space-y-4">
        <div>
          <FieldLabel
            label="Suggested profile"
            help="Choisissez un profil pour appliquer des reglages recommandes. Vous pourrez ajuster ensuite."
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {RAG_PROFILES.map((profile) => (
            <Card
              key={profile.id}
              className={cn(
                'flex h-full flex-col border border-white/60',
                selectedProfile === profile.id ? 'ring-2 ring-accent' : 'hover:shadow-glow'
              )}
            >
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted">{profile.tag}</p>
                <h4 className="mt-2 text-lg font-display">{profile.name}</h4>
                <p className="mt-2 text-sm text-muted">{profile.description}</p>
              </div>
              <div className="mt-auto pt-4">
                <Button
                  variant={selectedProfile === profile.id ? 'primary' : 'outline'}
                  onClick={() => handleProfileSelect(profile)}
                >
                  Apply profile
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
