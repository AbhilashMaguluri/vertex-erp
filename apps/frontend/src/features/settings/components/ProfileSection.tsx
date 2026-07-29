import { useQuery } from '@tanstack/react-query';
import { authService } from '@/features/auth/services/auth.service';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';

const ROW = 'flex items-center justify-between py-3 border-b border-border/60 last:border-0';
const LABEL = 'text-xs font-semibold text-muted-foreground';
const VALUE = 'text-xs font-bold text-foreground';

export function ProfileSection() {
  const { data: profile, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authService.getCurrentUser,
  });

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h3 className="text-base font-bold text-foreground">Profile</h3>
        <p className="text-xs text-muted-foreground">Your account identity, provisioned by institutional administration.</p>
      </div>

      {isLoading ? (
        <Skeleton className="h-56 rounded-xl" />
      ) : profile ? (
        <div className="rounded-xl border border-border/80 bg-muted/20 p-5">
          <div className={ROW}>
            <span className={LABEL}>Full Name</span>
            <span className={VALUE}>{profile.full_name || '—'}</span>
          </div>
          <div className={ROW}>
            <span className={LABEL}>Email Address</span>
            <span className={`${VALUE} font-mono`}>{profile.email}</span>
          </div>
          <div className={ROW}>
            <span className={LABEL}>Phone Number</span>
            <span className={VALUE}>{profile.phone || 'Not on file'}</span>
          </div>
          <div className={ROW}>
            <span className={LABEL}>Roles</span>
            <div className="flex gap-1">
              {profile.roles.map((r) => (
                <Badge key={r} variant="success">{r.replace('_', ' ')}</Badge>
              ))}
            </div>
          </div>
          {profile.last_login_at && (
            <div className={ROW}>
              <span className={LABEL}>Last Login</span>
              <span className={`${VALUE} font-mono`}>{new Date(profile.last_login_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      ) : null}

      <p className="text-xs text-muted-foreground leading-relaxed">
        To correct your official name, email, or other identity fields, contact your institutional administrator.
      </p>
    </div>
  );
}
