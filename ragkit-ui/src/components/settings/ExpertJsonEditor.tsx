import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface ExpertJsonEditorProps {
  jsonDraft: string;
  error: string | null;
  onChange: (value: string) => void;
  onFormat: () => void;
  onValidate: () => void;
}

export function ExpertJsonEditor({
  jsonDraft,
  error,
  onChange,
  onFormat,
  onValidate,
}: ExpertJsonEditorProps) {
  const { t } = useTranslation();
  const [touched, setTouched] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-display">{t('settings.expertJson.title')}</h3>
          <p className="text-sm text-muted">{t('settings.expertJson.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onFormat}>
            {t('common.actions.formatJson')}
          </Button>
          <Button variant="outline" onClick={onValidate}>
            {t('common.actions.validate')}
          </Button>
        </div>
      </div>
      <Textarea
        value={jsonDraft}
        onChange={(event) => {
          setTouched(true);
          onChange(event.target.value);
        }}
        rows={22}
        className="font-mono text-xs"
      />
      {error && touched ? (
        <div className="rounded-2xl bg-rose-50 p-4 text-xs text-rose-700">
          {error}
        </div>
      ) : null}
    </div>
  );
}
