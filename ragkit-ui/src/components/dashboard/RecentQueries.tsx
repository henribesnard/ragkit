import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchQueryLogs } from '@/api/metrics';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';

export function RecentQueries() {
  const { t } = useTranslation();
  const { data = [], isLoading } = useQuery({
    queryKey: ['query-logs'],
    queryFn: () => fetchQueryLogs(5, 0),
    refetchInterval: 30_000,
  });

  return (
    <Card className="lg:col-span-2">
      <CardTitle>{t('dashboard.recent.title')}</CardTitle>
      <CardDescription>{t('dashboard.recent.subtitle')}</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading && <p className="text-sm text-muted">{t('dashboard.recent.loading')}</p>}
        {!isLoading && data.length === 0 && (
          <p className="text-sm text-muted">{t('dashboard.recent.empty')}</p>
        )}
        {data.map((item: any, index: number) => (
          <div key={index} className="rounded-2xl bg-canvas p-4 text-sm">
            <p className="font-semibold">{item.query}</p>
            <div className="mt-1 flex items-center justify-between text-xs text-muted">
              <span>{item.intent || t('common.values.unknown')}</span>
              <span>{Math.round(item.latency_ms || 0)}ms</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
