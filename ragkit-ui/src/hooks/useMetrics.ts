import { useQuery } from '@tanstack/react-query';
import { fetchMetricsSummary } from '@/api/metrics';

export function useMetrics(period = '24h') {
  return useQuery({
    queryKey: ['metrics', period],
    queryFn: () => fetchMetricsSummary(period),
    refetchInterval: 60_000,
  });
}
