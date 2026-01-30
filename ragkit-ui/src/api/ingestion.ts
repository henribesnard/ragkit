import { apiClient } from './client';

export async function fetchIngestionStatus() {
  const response = await apiClient.get('/api/v1/admin/ingestion/status');
  return response.data;
}

export async function runIngestion(incremental = true) {
  const response = await apiClient.post('/api/v1/admin/ingestion/run', { incremental });
  return response.data;
}

export async function fetchIngestionHistory(limit = 10) {
  const response = await apiClient.get('/api/v1/admin/ingestion/history', { params: { limit } });
  return response.data;
}
