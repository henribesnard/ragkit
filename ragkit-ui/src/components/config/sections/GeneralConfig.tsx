import { useTranslation } from 'react-i18next';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { FieldLabel } from '@/components/ui/field-label';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function GeneralConfig({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const project = config?.project || {};
  return (
    <div className="space-y-6">
      <div>
        <FieldLabel
          label={t('wizard.project.nameLabel')}
          help={t('wizard.project.nameHelp')}
        />
        <Input
          value={project.name || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, name: event.target.value } })}
        />
      </div>
      <div>
        <FieldLabel
          label={t('wizard.project.descriptionLabel')}
          help={t('wizard.project.descriptionHelp')}
        />
        <Textarea
          rows={4}
          value={project.description || ''}
          onChange={(event) => onChange({ ...config, project: { ...project, description: event.target.value } })}
        />
      </div>
      <div>
        <FieldLabel
          label={t('wizard.project.environmentLabel')}
          help={t('wizard.project.environmentHelp')}
        />
        <Select
          value={project.environment || 'development'}
          onChange={(event) => onChange({ ...config, project: { ...project, environment: event.target.value } })}
        >
          <option value="development">{t('common.environments.development')}</option>
          <option value="staging">{t('common.environments.staging')}</option>
          <option value="production">{t('common.environments.production')}</option>
        </Select>
      </div>
    </div>
  );
}
