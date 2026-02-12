import { useQuery } from '@tanstack/react-query';
import { fetchHealthDetailed } from '@/api/health';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealthDetailed,
    refetchInterval: 30_000,
  });
}
