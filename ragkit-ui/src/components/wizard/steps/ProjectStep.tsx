import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
          label={t('wizard.project.nameLabel')}
          help={t('wizard.project.nameHelp')}
        />
        <Input
          placeholder={t('wizard.project.namePlaceholder')}
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
          label={t('wizard.project.descriptionLabel')}
          help={t('wizard.project.descriptionHelp')}
        />
        <Textarea
          placeholder={t('wizard.project.descriptionPlaceholder')}
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
          label={t('wizard.project.environmentLabel')}
          help={t('wizard.project.environmentHelp')}
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
          <option value="development">{t('common.environments.development')}</option>
          <option value="staging">{t('common.environments.staging')}</option>
          <option value="production">{t('common.environments.production')}</option>
        </Select>
      </div>

      <div className="space-y-4">
        <div>
          <FieldLabel
            label={t('wizard.project.profileLabel')}
            help={t('wizard.project.profileHelp')}
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
                <p className="text-xs uppercase tracking-[0.3em] text-muted">{t(profile.tagKey)}</p>
                <h4 className="mt-2 text-lg font-display">{t(profile.nameKey)}</h4>
                <p className="mt-2 text-sm text-muted">{t(profile.descriptionKey)}</p>
              </div>
              <div className="mt-auto pt-4">
                <Button
                  variant={selectedProfile === profile.id ? 'primary' : 'outline'}
                  onClick={() => handleProfileSelect(profile)}
                >
                  {t('wizard.project.applyProfile')}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
