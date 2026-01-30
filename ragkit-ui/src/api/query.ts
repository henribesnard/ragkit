import { apiClient } from './client';

export async function queryRag(payload: { query: string; history?: any[] }) {
  const response = await apiClient.post('/api/v1/query', payload);
  return response.data;
}
