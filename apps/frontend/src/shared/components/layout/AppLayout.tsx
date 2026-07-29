import { Outlet, useNavigate } from 'react-router-dom';
import { AppShell } from './AppShell';
import { useAuth } from '@/features/auth/hooks/useAuth';

/**
 * The real shell wrapper for every authenticated page — reads the signed-in
 * user from AuthContext instead of hardcoded placeholder props, and wires
 * the header's logout button to a real, full session teardown.
 */
export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <AppShell userRole={user?.roles[0] ?? 'STUDENT'} userName={user?.full_name ?? 'User'} onLogout={handleLogout}>
      <Outlet />
    </AppShell>
  );
}
