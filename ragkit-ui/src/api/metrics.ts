import { apiClient } from './client';

export async function fetchMetricsSummary(period = '24h') {
  const response = await apiClient.get('/api/v1/admin/metrics/summary', { params: { period } });
  return response.data;
}

export async function fetchMetricTimeseries(metric: string, period = '24h', interval = '1h') {
  const response = await apiClient.get(`/api/v1/admin/metrics/timeseries/${metric}`, {
    params: { period, interval },
  });
  return response.data;
}

export async function fetchQueryLogs(limit = 100, offset = 0) {
  const response = await apiClient.get('/api/v1/admin/metrics/queries', { params: { limit, offset } });
  return response.data;
}
