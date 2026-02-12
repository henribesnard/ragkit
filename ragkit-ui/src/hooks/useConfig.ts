import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchConfig, updateConfig } from '@/api/config';

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: fetchConfig,
  });
}

export function useUpdateConfig() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ config, validateOnly }: { config: Record<string, unknown>; validateOnly?: boolean }) =>
      updateConfig(config, validateOnly),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ['config'] });
    },
  });
}
