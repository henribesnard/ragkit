import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchQueryLogs } from '@/api/metrics';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { QueryLogEntry } from '@/types/api';

const PAGE_SIZE = 20;

export function Logs() {
  const [page, setPage] = useState(0);
  const { data = [], isLoading } = useQuery({
    queryKey: ['query-logs', page],
    queryFn: () => fetchQueryLogs(PAGE_SIZE, page * PAGE_SIZE),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>Query Logs</CardTitle>
        <CardDescription>Review recent queries, intents, and latency.</CardDescription>

        <div className="mt-6 space-y-3">
          {isLoading && <p className="text-sm text-muted">Loading logs...</p>}
          {!isLoading && data.length === 0 && (
            <p className="text-sm text-muted">No queries recorded yet.</p>
          )}
          {data.map((item: QueryLogEntry, index: number) => (
            <div key={`${item.timestamp}-${index}`} className="rounded-2xl bg-canvas p-4 text-sm">
              <div className="flex items-start justify-between gap-4">
                <p className="flex-1 font-semibold">{item.query}</p>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
                    item.success
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {item.success ? 'OK' : 'Error'}
                </span>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-muted">
                <span>Intent: {item.intent || 'unknown'}</span>
                <span>{Math.round(item.latency_ms)}ms</span>
              </div>
              {item.error && (
                <p className="mt-1 text-xs text-rose-600">{item.error}</p>
              )}
              <p className="mt-1 text-xs text-muted">
                {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
              </p>
            </div>
          ))}
        </div>

        {!isLoading && (
          <div className="mt-4 flex items-center justify-between">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <span className="text-xs text-muted">Page {page + 1}</span>
            <Button
              variant="outline"
              size="sm"
              disabled={data.length < PAGE_SIZE}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
