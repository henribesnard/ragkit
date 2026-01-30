import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useIngestionStatus, useRunIngestion } from '@/hooks/useIngestion';

export function IngestionStatus() {
  const { data, isLoading } = useIngestionStatus();
  const { mutate, isPending } = useRunIngestion();

  return (
    <Card>
      <CardTitle>Ingestion</CardTitle>
      <CardDescription>Track indexing progress.</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading ? (
          <p className="text-sm text-muted">Loading ingestion status...</p>
        ) : (
          <>
            <div className="flex items-center justify-between text-sm">
              <span>Running</span>
              <span className="font-semibold">{data?.is_running ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Pending documents</span>
              <span className="font-semibold">{data?.pending_documents ?? 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Total chunks</span>
              <span className="font-semibold">{data?.total_chunks ?? 0}</span>
            </div>
          </>
        )}
        <Button
          className="w-full"
          onClick={() => mutate(true)}
          disabled={isPending || data?.is_running}
        >
          {data?.is_running ? 'Ingestion running' : 'Run ingestion'}
        </Button>
      </div>
    </Card>
  );
}
