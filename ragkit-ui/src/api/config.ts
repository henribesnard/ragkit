import { apiClient } from './client';

export async function fetchConfig() {
  const response = await apiClient.get('/api/v1/admin/config');
  return response.data;
}

export async function updateConfig(config: Record<string, unknown>, validateOnly = false) {
  const response = await apiClient.put('/api/v1/admin/config', {
    config,
    validate_only: validateOnly,
  });
  return response.data;
}

export async function validateConfig(config: Record<string, unknown>) {
  const response = await apiClient.post('/api/v1/admin/config/validate', {
    config,
    validate_only: true,
  });
  return response.data;
}
