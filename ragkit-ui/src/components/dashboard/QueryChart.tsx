import { useTranslation } from 'react-i18next';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface QueryChartProps {
  data?: Array<{ timestamp: string; value: number }>;
}

export function QueryChart({ data = [] }: QueryChartProps) {
  const { t } = useTranslation();
  return (
    <Card className="h-full">
      <CardTitle>{t('dashboard.queryChart.title')}</CardTitle>
      <CardDescription>{t('dashboard.queryChart.subtitle')}</CardDescription>
      <div className="mt-6 h-56">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center rounded-2xl bg-canvas text-sm text-muted">
            {t('dashboard.metrics.noData')}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <XAxis dataKey="timestamp" hide />
              <YAxis hide />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#0e7490" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
