import { cn } from '@/utils/cn';

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
}

const styles: Record<string, string> = {
  healthy: 'bg-emerald-100 text-emerald-700',
  degraded: 'bg-amber-100 text-amber-700',
  unhealthy: 'bg-rose-100 text-rose-700',
  unknown: 'bg-slate-100 text-slate-600',
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={cn('rounded-full px-3 py-1 text-xs font-semibold', styles[status])}>
      {status}
    </span>
  );
}
