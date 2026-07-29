import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Spinner } from '@/shared/components/ui/Spinner';

/**
 * For Login / Forgot Password / Reset Password. An already-authenticated
 * user must never see these — send them straight into the app (or the
 * forced password-change gate, if that's still pending).
 */
export function GuestRoute() {
  const { status, user } = useAuth();

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (status === 'authenticated') {
    return <Navigate to={user?.force_password_change ? '/change-password' : '/dashboard'} replace />;
  }

  return <Outlet />;
}
