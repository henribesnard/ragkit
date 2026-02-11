import { useTranslation } from 'react-i18next';
import { useMetrics } from '@/hooks/useMetrics';
import { useIngestionStatus } from '@/hooks/useIngestion';
import { useWebSocket } from '@/hooks/useWebSocket';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { HealthStatus } from '@/components/dashboard/HealthStatus';
import { IngestionStatus } from '@/components/dashboard/IngestionStatus';
import { RecentQueries } from '@/components/dashboard/RecentQueries';
import { MetricsDashboard } from '@/components/dashboard/MetricsDashboard';

export function Dashboard() {
  const { t } = useTranslation();
  const { data: metrics } = useMetrics('24h');
  const { data: ingestionStatus } = useIngestionStatus();
  const { lastMessage } = useWebSocket();

  return (
    <div className="space-y-6">
      {lastMessage && (
        <div className="rounded-3xl bg-white/70 px-6 py-4 text-xs text-muted shadow-soft">
          {t('dashboard.liveEvent')}:
          <span className="font-semibold text-ink"> {lastMessage.type}</span>
        </div>
      )}
      <StatsCards metrics={metrics} ingestionStatus={ingestionStatus} />
      <MetricsDashboard />
      <div className="grid gap-6 lg:grid-cols-2">
        <HealthStatus />
        <IngestionStatus />
      </div>
      <RecentQueries />
    </div>
  );
}
