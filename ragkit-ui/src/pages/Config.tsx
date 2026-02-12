import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useConfig, useUpdateConfig } from '@/hooks/useConfig';
import { validateConfig } from '@/api/config';
import { AdvancedConfigTabs } from '@/components/config/AdvancedConfigTabs';
import { ExpertiseLevelSelector } from '@/components/settings/ExpertiseLevelSelector';
import { ProfileSelector } from '@/components/settings/ProfileSelector';
import { IntermediateSettings } from '@/components/settings/IntermediateSettings';
import { ExpertJsonEditor } from '@/components/settings/ExpertJsonEditor';
import { applyProfilePatch } from '@/data/profiles';
import { useConfigStore } from '@/stores/configStore';

export function Config() {
  const { t } = useTranslation();
  const { data, isLoading } = useConfig();
  const { mutate: updateConfig, isPending } = useUpdateConfig();
  const { config, expertiseLevel, jsonDraft, jsonError, setConfig, setExpertiseLevel, setJsonDraft } =
    useConfigStore();
  const [serverSnapshot, setServerSnapshot] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  useEffect(() => {
    if (data?.config) {
      setConfig(data.config);
      setServerSnapshot(JSON.stringify(data.config ?? {}));
    }
  }, [data, setConfig]);

  const hasChanges = useMemo(() => {
    if (!serverSnapshot) {
      return false;
    }
    return JSON.stringify(config ?? {}) !== serverSnapshot;
  }, [config, serverSnapshot]);

  const handleSave = () => {
    updateConfig({ config, validateOnly: false });
    setValidationMessage(null);
  };

  const handleExport = () => {
    window.location.href = '/api/v1/admin/config/export';
  };

  const handleValidate = async () => {
    try {
      const result = await validateConfig(config);
      if (result?.valid) {
        setValidationMessage(t('config.validation.valid'));
      } else {
        setValidationMessage(result?.errors?.join(' | ') || t('config.validation.invalid'));
      }
    } catch (error: any) {
      setValidationMessage(error?.message || t('config.validation.unable'));
    }
  };

  if (isLoading) {
    return <p className="text-sm text-muted">{t('config.loading')}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-display">{t('config.title')}</h2>
          <p className="text-sm text-muted">{t('config.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            {t('config.actions.export')}
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || isPending}>
            {isPending ? t('common.actions.saving') : t('common.actions.saveChanges')}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
        <ExpertiseLevelSelector value={expertiseLevel} onChange={setExpertiseLevel} />
        <div className="space-y-6">
          {expertiseLevel === 'simple' ? (
            <ProfileSelector
              selectedId={selectedProfile}
              onSelect={(profile) => {
                setSelectedProfile(profile.id);
                const nextConfig = applyProfilePatch(config, profile);
                setConfig(nextConfig);
              }}
            />
          ) : null}
          {expertiseLevel === 'intermediate' ? (
            <IntermediateSettings
              config={config}
              onChange={(next) => {
                setConfig(next);
              }}
            />
          ) : null}
          {expertiseLevel === 'expert' ? (
            <div className="space-y-6">
              <ExpertJsonEditor
                jsonDraft={jsonDraft}
                error={jsonError}
                onChange={(value) => setJsonDraft(value)}
                onFormat={() => {
                  try {
                    const formatted = JSON.stringify(JSON.parse(jsonDraft || '{}'), null, 2);
                    setJsonDraft(formatted);
                  } catch {
                    setValidationMessage(t('config.validation.formatError'));
                  }
                }}
                onValidate={handleValidate}
              />
              <div className="rounded-3xl bg-white/60 p-6 shadow-soft">
                <div className="mb-4">
                  <h3 className="text-lg font-display">{t('config.advanced.title')}</h3>
                  <p className="text-xs text-muted">{t('config.advanced.subtitle')}</p>
                </div>
                <AdvancedConfigTabs
                  config={config}
                  onChange={(next) => {
                    setConfig(next);
                  }}
                />
              </div>
            </div>
          ) : null}
        </div>
      </div>
      {validationMessage ? (
        <p className="rounded-2xl bg-slate-900/90 p-4 text-xs text-white">{validationMessage}</p>
      ) : null}
    </div>
  );
}
