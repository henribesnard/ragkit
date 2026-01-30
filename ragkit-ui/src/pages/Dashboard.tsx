import { useQuery } from '@tanstack/react-query';
import { fetchMetricTimeseries } from '@/api/metrics';
import { QueryChart } from '@/components/dashboard/QueryChart';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { HealthStatus } from '@/components/dashboard/HealthStatus';
import { IngestionStatus } from '@/components/dashboard/IngestionStatus';
import { RecentQueries } from '@/components/dashboard/RecentQueries';
import { useMetrics } from '@/hooks/useMetrics';
import { useIngestionStatus } from '@/hooks/useIngestion';
import { useWebSocket } from '@/hooks/useWebSocket';

export function Dashboard() {
  const { data: metrics } = useMetrics('24h');
  const { data: ingestionStatus } = useIngestionStatus();
  const { lastMessage } = useWebSocket();
  const { data: timeseries = [] } = useQuery({
    queryKey: ['metric-timeseries', 'query_count'],
    queryFn: () => fetchMetricTimeseries('query_count', '24h', '1h'),
  });

  const chartData = (timeseries as any[]).map((point) => ({
    timestamp: point.timestamp,
    value: point.value,
  }));

  return (
    <div className="space-y-6">
      {lastMessage && (
        <div className="rounded-3xl bg-white/70 px-6 py-4 text-xs text-muted shadow-soft">
          Live event: <span className="font-semibold text-ink">{lastMessage.type}</span>
        </div>
      )}
      <StatsCards metrics={metrics} ingestionStatus={ingestionStatus} />
      <div className="grid gap-6 lg:grid-cols-2">
        <QueryChart data={chartData} />
        <HealthStatus />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <IngestionStatus />
        <RecentQueries />
      </div>
    </div>
  );
}
