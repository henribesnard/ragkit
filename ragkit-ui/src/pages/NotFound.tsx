import { useTranslation } from 'react-i18next';

export function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="rounded-3xl bg-white/80 p-8 text-center shadow-soft">
      <h2 className="text-2xl font-display">{t('notFound.title')}</h2>
      <p className="mt-2 text-sm text-muted">{t('notFound.subtitle')}</p>
    </div>
  );
}
