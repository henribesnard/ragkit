import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { fetchMetricTimeseries } from '@/api/metrics';
import { useMetrics } from '@/hooks/useMetrics';

const formatValue = (value: number | null | undefined, unit?: string) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--';
  }
  const formatted = unit === '%' ? value.toFixed(0) : value.toFixed(1);
  return unit ? `${formatted}${unit}` : formatted;
};

const MetricCard = ({
  title,
  description,
  value,
  unit,
}: {
  title: string;
  description: string;
  value: number | null | undefined;
  unit?: string;
}) => (
  <Card>
    <CardTitle>{title}</CardTitle>
    <CardDescription>{description}</CardDescription>
    <p className="mt-4 text-3xl font-semibold">{formatValue(value, unit)}</p>
  </Card>
);

const ChartCard = ({
  title,
  description,
  data,
  color,
  emptyLabel,
}: {
  title: string;
  description: string;
  data: Array<{ timestamp: string; value: number }>;
  color: string;
  emptyLabel: string;
}) => (
  <Card className="h-full">
    <CardTitle>{title}</CardTitle>
    <CardDescription>{description}</CardDescription>
    <div className="mt-6 h-56">
      {data.length === 0 ? (
        <div className="flex h-full items-center justify-center rounded-2xl bg-canvas text-sm text-muted">
          {emptyLabel}
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="timestamp" hide />
            <YAxis hide />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke={color} strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  </Card>
);

export function MetricsDashboard() {
  const { t } = useTranslation();
  const { data: metrics } = useMetrics('24h');
  const { data: latencySeries = [] } = useQuery({
    queryKey: ['metric-timeseries', 'query_latency_ms'],
    queryFn: () => fetchMetricTimeseries('query_latency_ms', '24h', '1h'),
  });
  const { data: throughputSeries = [] } = useQuery({
    queryKey: ['metric-timeseries', 'query_count'],
    queryFn: () => fetchMetricTimeseries('query_count', '24h', '1h'),
  });

  const latencyData = (latencySeries as any[]).map((point) => ({
    timestamp: point.timestamp,
    value: point.value,
  }));
  const throughputData = (throughputSeries as any[]).map((point) => ({
    timestamp: point.timestamp,
    value: point.value,
  }));

  const successRate =
    metrics?.queries?.total && metrics?.queries?.total > 0
      ? (metrics.queries.success / metrics.queries.total) * 100
      : null;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title={t('dashboard.metrics.latencyP95')}
          description={t('dashboard.metrics.latencyP95Help')}
          value={metrics?.queries?.p95_latency_ms}
          unit="ms"
        />
        <MetricCard
          title={t('dashboard.metrics.successRate')}
          description={t('dashboard.metrics.successRateHelp')}
          value={successRate}
          unit="%"
        />
        <MetricCard
          title={t('dashboard.metrics.cost')}
          description={t('dashboard.metrics.costHelp')}
          value={null}
          unit="$"
        />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title={t('dashboard.metrics.latencyTrend')}
          description={t('dashboard.metrics.latencyTrendHelp')}
          data={latencyData}
          color="#0e7490"
          emptyLabel={t('dashboard.metrics.noData')}
        />
        <ChartCard
          title={t('dashboard.metrics.queryVolume')}
          description={t('dashboard.metrics.queryVolumeHelp')}
          data={throughputData}
          color="#f97316"
          emptyLabel={t('dashboard.metrics.noData')}
        />
      </div>
    </div>
  );
}
