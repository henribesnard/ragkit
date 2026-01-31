import { Navigate, useLocation } from 'react-router-dom';
import { useStatus } from '@/hooks/useStatus';

export function SetupGuard({ children }: { children: React.ReactNode }) {
  const { data: status, isLoading } = useStatus();
  const location = useLocation();

  if (isLoading) return null;

  if (status?.setup_mode && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }

  return <>{children}</>;
}
