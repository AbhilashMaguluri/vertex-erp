import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService, SessionInfo } from '@/features/auth/services/auth.service';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { KeyRound, Monitor, ShieldCheck } from 'lucide-react';

function describeSession(s: SessionInfo): string {
  const ua = s.user_agent || '';
  if (/mobile/i.test(ua)) return 'Mobile device';
  if (/chrome/i.test(ua)) return 'Chrome browser';
  if (/firefox/i.test(ua)) return 'Firefox browser';
  if (/safari/i.test(ua)) return 'Safari browser';
  return ua ? ua.slice(0, 40) : 'Unknown device';
}

export function SecuritySection() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery<SessionInfo[]>({
    queryKey: ['auth', 'sessions'],
    queryFn: authService.getSessions,
  });

  const revokeMutation = useMutation({
    mutationFn: (sessionId: string) => authService.revokeSession(sessionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth', 'sessions'] }),
  });

  const others = (sessions ?? []).filter((s) => !s.is_current);

  return (
    <div className="space-y-8 max-w-xl">
      <div>
        <h3 className="text-base font-bold text-foreground">Security &amp; Account</h3>
        <p className="text-xs text-muted-foreground">Manage your password and active sign-in sessions.</p>
      </div>

      {/* Change password */}
      <div className="rounded-xl border border-border/80 p-5 bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-bold text-foreground flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-primary" /> Password
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Changing your password signs out every other device automatically.
          </p>
        </div>
        <Button size="sm" onClick={() => navigate('/change-password')} className="shrink-0">
          Change Password
        </Button>
      </div>

      {/* Active sessions */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-bold text-foreground flex items-center gap-2">
            <Monitor className="h-4 w-4 text-primary" /> Active Sessions
          </p>
          {others.length > 0 && (
            <Button
              size="sm"
              variant="outline"
              isLoading={revokeMutation.isPending}
              onClick={() => others.forEach((s) => revokeMutation.mutate(s.id))}
            >
              Log Out Other Devices
            </Button>
          )}
        </div>

        {isLoading ? (
          <Skeleton className="h-32 rounded-xl" />
        ) : !sessions || sessions.length === 0 ? (
          <EmptyState icon={ShieldCheck} title="No active sessions" description="You have no other active sign-ins." />
        ) : (
          <div className="space-y-2">
            {sessions.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-xl border border-border/70 bg-muted/20 p-3.5">
                <div className="space-y-0.5 min-w-0">
                  <p className="text-xs font-bold text-foreground flex items-center gap-2">
                    {describeSession(s)}
                    {s.is_current && <Badge variant="success" className="text-[9px] py-0">This device</Badge>}
                  </p>
                  <p className="text-[11px] font-mono text-muted-foreground truncate">
                    {s.ip_address || 'Unknown IP'} • signed in {new Date(s.created_at).toLocaleString()}
                  </p>
                </div>
                {!s.is_current && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-rose-600 hover:bg-rose-500/10 shrink-0"
                    isLoading={revokeMutation.isPending && revokeMutation.variables === s.id}
                    onClick={() => revokeMutation.mutate(s.id)}
                  >
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
