import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchIngestionHistory, fetchIngestionStatus, runIngestion } from '@/api/ingestion';

export function useIngestionStatus() {
  return useQuery({
    queryKey: ['ingestion', 'status'],
    queryFn: fetchIngestionStatus,
    refetchInterval: 20_000,
  });
}

export function useIngestionHistory(limit = 10) {
  return useQuery({
    queryKey: ['ingestion', 'history', limit],
    queryFn: () => fetchIngestionHistory(limit),
  });
}

export function useRunIngestion() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (incremental: boolean) => runIngestion(incremental),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ['ingestion', 'status'] });
      client.invalidateQueries({ queryKey: ['ingestion', 'history'] });
    },
  });
}
