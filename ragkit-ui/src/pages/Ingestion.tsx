import { useTranslation } from 'react-i18next';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useIngestionStatus, useIngestionHistory, useRunIngestion } from '@/hooks/useIngestion';

export function Ingestion() {
  const { t } = useTranslation();
  const { data: status, isLoading } = useIngestionStatus();
  const { data: history = [] } = useIngestionHistory(20);
  const { mutate, isPending } = useRunIngestion();

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>{t('ingestion.control.title')}</CardTitle>
        <CardDescription>{t('ingestion.control.subtitle')}</CardDescription>

        {isLoading ? (
          <p className="mt-6 text-sm text-muted">{t('common.loading')}</p>
        ) : (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatusItem
                label={t('ingestion.status.running')}
                value={status?.is_running ? t('common.values.yes') : t('common.values.no')}
              />
              <StatusItem label={t('ingestion.status.pendingDocs')} value={status?.pending_documents ?? 0} />
              <StatusItem label={t('ingestion.status.totalDocs')} value={status?.total_documents ?? 0} />
              <StatusItem label={t('ingestion.status.totalChunks')} value={status?.total_chunks ?? 0} />
            </div>

            <div className="flex gap-2">
              <Button onClick={() => mutate(true)} disabled={isPending || status?.is_running}>
                {status?.is_running
                  ? t('ingestion.actions.running')
                  : t('ingestion.actions.runIncremental')}
              </Button>
              <Button variant="outline" onClick={() => mutate(false)} disabled={isPending || status?.is_running}>
                {t('ingestion.actions.fullReindex')}
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>{t('ingestion.history.title')}</CardTitle>
        <CardDescription>{t('ingestion.history.subtitle')}</CardDescription>

        <div className="mt-6 space-y-3">
          {history.length === 0 && <p className="text-sm text-muted">{t('ingestion.history.empty')}</p>}
          {history.map((run: any) => {
            const statusLabelMap: Record<string, string> = {
              completed: t('ingestion.history.status.completed'),
              failed: t('ingestion.history.status.failed'),
              running: t('ingestion.history.status.running'),
            };
            const statusLabel = statusLabelMap[run.status] || run.status;
            return (
              <div key={run.id} className="flex items-center justify-between rounded-2xl bg-canvas p-4 text-sm">
                <div>
                  <span
                    className={`mr-2 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                      run.status === 'completed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {statusLabel}
                  </span>
                  <span className="text-muted">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : ''}
                  </span>
                </div>
                <div className="text-xs text-muted">
                  {run.stats
                    ? t('ingestion.history.stats', {
                        docs: run.stats.documents_loaded ?? 0,
                        chunks: run.stats.chunks_stored ?? 0,
                      })
                    : ''}
                </div>
              </div>
            );
          })}
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
