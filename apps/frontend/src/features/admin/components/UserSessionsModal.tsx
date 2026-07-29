import * as React from 'react';
import { Modal } from '@/shared/components/ui/Modal';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Spinner } from '@/shared/components/ui/Spinner';
import { userAdminService, SessionInfo } from '../services/admin.service';
import { Monitor } from 'lucide-react';

interface UserSessionsModalProps {
  open: boolean;
  onClose: () => void;
  userId: string | null;
  userEmail: string;
}

export function UserSessionsModal({ open, onClose, userId, userEmail }: UserSessionsModalProps) {
  const [sessions, setSessions] = React.useState<SessionInfo[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isForcing, setIsForcing] = React.useState(false);

  const load = React.useCallback(() => {
    if (!userId) return;
    setIsLoading(true);
    userAdminService
      .listSessions(userId)
      .then(setSessions)
      .finally(() => setIsLoading(false));
  }, [userId]);

  React.useEffect(() => {
    if (open) load();
  }, [open, load]);

  const handleForceLogout = async () => {
    if (!userId) return;
    setIsForcing(true);
    try {
      await userAdminService.forceLogout(userId);
      await load();
    } finally {
      setIsForcing(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Active Sessions" description={userEmail}>
      <div className="space-y-3">
        {isLoading ? (
          <div className="py-6"><Spinner /></div>
        ) : sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground py-4 text-center">No active sessions.</p>
        ) : (
          <ul className="space-y-2 max-h-72 overflow-y-auto">
            {sessions.map((s) => (
              <li key={s.id} className="flex items-center justify-between rounded-md border border-border p-2.5 text-xs">
                <div className="flex items-center gap-2 min-w-0">
                  <Monitor className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  <div className="min-w-0">
                    <p className="truncate text-foreground">{s.user_agent || 'Unknown device'}</p>
                    <p className="text-muted-foreground">
                      Signed in {new Date(s.created_at).toLocaleString()} · {s.ip_address || 'unknown IP'}
                    </p>
                  </div>
                </div>
                {s.remember_me && <Badge variant="secondary">Remember me</Badge>}
              </li>
            ))}
          </ul>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button
            variant="destructive"
            onClick={handleForceLogout}
            disabled={isForcing || sessions.length === 0}
          >
            {isForcing ? 'Signing out...' : 'Force Logout (All Devices)'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
