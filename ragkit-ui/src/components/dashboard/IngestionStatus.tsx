import { useTranslation } from 'react-i18next';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useIngestionStatus, useRunIngestion } from '@/hooks/useIngestion';

export function IngestionStatus() {
  const { t } = useTranslation();
  const { data, isLoading } = useIngestionStatus();
  const { mutate, isPending } = useRunIngestion();

  return (
    <Card>
      <CardTitle>{t('dashboard.ingestion.title')}</CardTitle>
      <CardDescription>{t('dashboard.ingestion.subtitle')}</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading ? (
          <p className="text-sm text-muted">{t('dashboard.ingestion.loading')}</p>
        ) : (
          <>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.ingestion.running')}</span>
              <span className="font-semibold">
                {data?.is_running ? t('common.values.yes') : t('common.values.no')}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.ingestion.pending')}</span>
              <span className="font-semibold">{data?.pending_documents ?? 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.ingestion.totalChunks')}</span>
              <span className="font-semibold">{data?.total_chunks ?? 0}</span>
            </div>
          </>
        )}
        <Button
          className="w-full"
          onClick={() => mutate(true)}
          disabled={isPending || data?.is_running}
        >
          {data?.is_running ? t('dashboard.ingestion.runningLabel') : t('dashboard.ingestion.runLabel')}
        </Button>
      </div>
    </Card>
  );
}
