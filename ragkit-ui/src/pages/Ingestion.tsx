import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useIngestionStatus, useIngestionHistory, useRunIngestion } from '@/hooks/useIngestion';

export function Ingestion() {
  const { data: status, isLoading } = useIngestionStatus();
  const { data: history = [] } = useIngestionHistory(20);
  const { mutate, isPending } = useRunIngestion();

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>Ingestion Control</CardTitle>
        <CardDescription>Monitor and trigger ingestion runs.</CardDescription>

        {isLoading ? (
          <p className="mt-6 text-sm text-muted">Loading status...</p>
        ) : (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatusItem label="Running" value={status?.is_running ? 'Yes' : 'No'} />
              <StatusItem label="Pending docs" value={status?.pending_documents ?? 0} />
              <StatusItem label="Total docs" value={status?.total_documents ?? 0} />
              <StatusItem label="Total chunks" value={status?.total_chunks ?? 0} />
            </div>

            <div className="flex gap-2">
              <Button onClick={() => mutate(true)} disabled={isPending || status?.is_running}>
                {status?.is_running ? 'Running...' : 'Run incremental'}
              </Button>
              <Button variant="outline" onClick={() => mutate(false)} disabled={isPending || status?.is_running}>
                Full re-index
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>Run History</CardTitle>
        <CardDescription>Previous ingestion runs.</CardDescription>

        <div className="mt-6 space-y-3">
          {history.length === 0 && <p className="text-sm text-muted">No ingestion runs recorded yet.</p>}
          {history.map((run: any) => (
            <div key={run.id} className="flex items-center justify-between rounded-2xl bg-canvas p-4 text-sm">
              <div>
                <span className={`mr-2 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                  run.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-rose-100 text-rose-800'
                }`}>
                  {run.status}
                </span>
                <span className="text-muted">{run.started_at ? new Date(run.started_at).toLocaleString() : ''}</span>
              </div>
              <div className="text-xs text-muted">
                {run.stats
                  ? `${run.stats.documents_loaded ?? 0} docs / ${run.stats.chunks_stored ?? 0} chunks`
                  : ''}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function StatusItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl bg-canvas p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
