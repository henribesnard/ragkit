import { useQuery } from '@tanstack/react-query';
import { fetchQueryLogs } from '@/api/metrics';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';

export function RecentQueries() {
  const { data = [], isLoading } = useQuery({
    queryKey: ['query-logs'],
    queryFn: () => fetchQueryLogs(5, 0),
    refetchInterval: 30_000,
  });

  return (
    <Card className="lg:col-span-2">
      <CardTitle>Recent queries</CardTitle>
      <CardDescription>Latest user questions with latency.</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading && <p className="text-sm text-muted">Loading queries...</p>}
        {!isLoading && data.length === 0 && (
          <p className="text-sm text-muted">No queries recorded yet.</p>
        )}
        {data.map((item: any, index: number) => (
          <div key={index} className="rounded-2xl bg-canvas p-4 text-sm">
            <p className="font-semibold">{item.query}</p>
            <div className="mt-1 flex items-center justify-between text-xs text-muted">
              <span>{item.intent || 'unknown'}</span>
              <span>{Math.round(item.latency_ms || 0)}ms</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
