import { useHealth } from '@/hooks/useHealth';
import { Card, CardDescription, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/shared/StatusBadge';

export function HealthStatus() {
  const { data, isLoading } = useHealth();
  const components = data?.components || {};

  return (
    <Card>
      <CardTitle>System health</CardTitle>
      <CardDescription>Key services status snapshot.</CardDescription>
      <div className="mt-6 space-y-3">
        {isLoading && <p className="text-sm text-muted">Checking health...</p>}
        {!isLoading && Object.keys(components).length === 0 && (
          <p className="text-sm text-muted">No health data available.</p>
        )}
        {Object.entries(components).map(([name, info]: any) => (
          <div key={name} className="flex items-center justify-between">
            <span className="text-sm capitalize">{name.replace('_', ' ')}</span>
            <StatusBadge status={info.status || 'unknown'} />
          </div>
        ))}
      </div>
    </Card>
  );
}
