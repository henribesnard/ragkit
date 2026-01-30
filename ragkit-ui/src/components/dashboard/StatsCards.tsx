import { Card, CardDescription, CardTitle } from '@/components/ui/card';

interface StatsCardsProps {
  metrics?: any;
  ingestionStatus?: any;
}

export function StatsCards({ metrics, ingestionStatus }: StatsCardsProps) {
  const documents = metrics?.ingestion?.total_documents ?? 0;
  const chunks = metrics?.ingestion?.total_chunks ?? 0;
  const queries = metrics?.queries?.total ?? 0;
  const latency = metrics?.queries?.avg_latency_ms ?? 0;
  const pending = ingestionStatus?.pending_documents ?? 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardTitle>Documents</CardTitle>
        <CardDescription>{pending} pending</CardDescription>
        <p className="mt-4 text-3xl font-semibold">{documents}</p>
      </Card>
      <Card>
        <CardTitle>Chunks indexed</CardTitle>
        <CardDescription>Vector store coverage</CardDescription>
        <p className="mt-4 text-3xl font-semibold">{chunks}</p>
      </Card>
      <Card>
        <CardTitle>Queries (24h)</CardTitle>
        <CardDescription>Success rate {metrics?.queries?.success && metrics?.queries?.total ? `${Math.round((metrics.queries.success / metrics.queries.total) * 100)}%` : '--'}</CardDescription>
        <p className="mt-4 text-3xl font-semibold">{queries}</p>
      </Card>
      <Card>
        <CardTitle>Avg latency</CardTitle>
        <CardDescription>Across all queries</CardDescription>
        <p className="mt-4 text-3xl font-semibold">{Math.round(latency)}ms</p>
      </Card>
    </div>
  );
}
