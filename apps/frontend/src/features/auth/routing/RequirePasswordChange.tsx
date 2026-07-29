import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Mirrors the backend's PASSWORD_CHANGE_REQUIRED gate on the client: a user
 * who hasn't cleared force_password_change cannot reach any real workspace
 * route, only /change-password itself.
 */
export function RequirePasswordChange() {
  const { user } = useAuth();

  if (user?.force_password_change) {
    return <Navigate to="/change-password" replace />;
  }

  return <Outlet />;
}
