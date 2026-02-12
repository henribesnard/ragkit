import { apiClient } from './client';

export async function fetchHealthDetailed() {
  const response = await apiClient.get('/api/v1/admin/health/detailed');
  return response.data;
}
