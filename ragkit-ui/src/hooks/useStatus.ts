import { useQuery } from '@tanstack/react-query';
import { fetchStatus } from '@/api/config';

interface ServerStatus {
  configured: boolean;
  setup_mode: boolean;
  version: string;
  project: string;
  components: Record<string, boolean>;
}

export function useStatus() {
  return useQuery<ServerStatus>({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: 10_000,
  });
}
