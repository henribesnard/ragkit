import { useTranslation } from 'react-i18next';
import { useHealth } from '@/hooks/useHealth';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/shared/StatusBadge';

export function HealthStatus() {
  const { t } = useTranslation();
  const { data, isLoading } = useHealth();
  const components = data?.components || {};

  return (
    <Card>
      <CardTitle>{t('dashboard.health.title')}</CardTitle>
      <CardDescription>{t('dashboard.health.subtitle')}</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading && <p className="text-sm text-muted">{t('dashboard.health.loading')}</p>}
        {!isLoading && Object.keys(components).length === 0 && (
          <p className="text-sm text-muted">{t('dashboard.health.empty')}</p>
        )}
        {Object.entries(components).map(([name, info]: any) => (
          <div key={name} className="flex items-center justify-between">
            <span className="text-sm capitalize">{name.replace('_', ' ')}</span>
            <StatusBadge status={info.status || 'unknown'} />
          </div>
        ))}
      </div>
    </Card>
  );
}
