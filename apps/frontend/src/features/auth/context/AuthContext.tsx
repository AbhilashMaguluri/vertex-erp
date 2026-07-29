import * as React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { authService, UserSummary, UserProfile } from '../services/auth.service';
import { setAccessToken } from '@/shared/lib/axios';
import { LoginFormData } from '../schemas/auth.schema';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthContextValue {
  status: AuthStatus;
  user: UserSummary | null;
  login: (credentials: LoginFormData) => Promise<UserSummary>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

function toSummary(profile: UserProfile): UserSummary {
  return {
    id: profile.id,
    email: profile.email,
    full_name: profile.full_name,
    roles: profile.roles,
    permissions: profile.permissions,
    department_id: profile.department_id,
    force_password_change: profile.force_password_change,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = React.useState<AuthStatus>('loading');
  const [user, setUser] = React.useState<UserSummary | null>(null);
  const queryClient = useQueryClient();

  // Restore a session on page load using the httpOnly refresh cookie — the
  // access token only ever lives in memory, so a hard refresh always starts
  // from zero and must re-derive auth state from the server, not assume it.
  React.useEffect(() => {
    let cancelled = false;
    authService
      .refresh()
      .then((res) => {
        if (cancelled) return;
        setUser(res.user);
        setStatus('authenticated');
      })
      .catch(() => {
        if (cancelled) return;
        setAccessToken(null);
        setUser(null);
        setStatus('unauthenticated');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(async (credentials: LoginFormData) => {
    const res = await authService.login(credentials);
    setUser(res.user);
    setStatus('authenticated');
    return res.user;
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setAccessToken(null);
      setUser(null);
      setStatus('unauthenticated');
      queryClient.clear();
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch {
        // Storage may be unavailable — auth state above is already cleared.
      }
    }
  }, [queryClient]);

  const refreshUser = React.useCallback(async () => {
    const profile = await authService.getCurrentUser();
    setUser(toSummary(profile));
  }, []);

  const hasRole = React.useCallback((role: string) => !!user?.roles.includes(role), [user]);
  const hasAnyRole = React.useCallback(
    (roles: string[]) => !!user && roles.some((r) => user.roles.includes(r)),
    [user]
  );
  const hasPermission = React.useCallback(
    (permission: string) => !!user?.permissions.includes(permission),
    [user]
  );

  const value = React.useMemo<AuthContextValue>(
    () => ({ status, user, login, logout, hasRole, hasAnyRole, hasPermission, refreshUser }),
    [status, user, login, logout, hasRole, hasAnyRole, hasPermission, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
