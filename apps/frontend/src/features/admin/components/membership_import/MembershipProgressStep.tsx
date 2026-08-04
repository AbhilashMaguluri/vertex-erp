import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, UserPlus, Link2, Save, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { cn } from '@/shared/utils/cn';
import { membershipImportService } from '../../services/membershipImport.service';

const PHASE_ICONS: Record<string, React.ElementType> = {
  QUEUED: Loader2,
  STUDENTS: UserPlus,
  MEMBERSHIPS: Link2,
  COMPLETED: Save,
  FAILED: AlertTriangle,
};

const PHASE_ORDER = ['QUEUED', 'STUDENTS', 'MEMBERSHIPS'];

const PHASE_LABELS: Record<string, string> = {
  QUEUED: 'Queued',
  STUDENTS: 'Creating student accounts',
  MEMBERSHIPS: 'Assigning student memberships',
};

interface MembershipProgressStepProps {
  batchId: string;
  onDone: () => void;
  onFailed: (message: string) => void;
}

export function MembershipProgressStep({ batchId, onDone, onFailed }: MembershipProgressStepProps) {
  const { data: progress } = useQuery({
    queryKey: ['admin', 'membership-imports', batchId, 'progress'],
    queryFn: () => membershipImportService.getProgress(batchId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'COMPLETED' || status === 'FAILED' ? false : 1000;
    },
  });

  React.useEffect(() => {
    if (progress?.status === 'COMPLETED') onDone();
    if (progress?.status === 'FAILED') onFailed(progress.error || 'The import failed. Changes were rolled back.');
  }, [progress?.status, progress?.error, onDone, onFailed]);

  const percent = progress?.percent ?? 0;
  const currentPhase = progress?.phase ?? 'QUEUED';
  const currentIndex = PHASE_ORDER.indexOf(currentPhase);

  return (
    <Card className="mx-auto max-w-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-base">Executing Membership Import…</CardTitle>
        <CardDescription>
          This runs inside a single database transaction — if any error occurs, all changes are rolled back.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        <div>
          <div className="mb-2 flex items-center justify-between text-xs font-bold">
            <span className="text-foreground">{progress?.message ?? 'Preparing import…'}</span>
            <span className="font-mono text-primary">{percent}%</span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-muted/60">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary to-primary/80 transition-all duration-500 ease-out"
              style={{ width: `${percent}%` }}
            />
          </div>
          {progress && progress.total > 0 && (
            <p className="mt-1.5 text-right text-[11px] font-medium text-muted-foreground">
              {progress.processed} / {progress.total}
            </p>
          )}
        </div>

        <ol className="space-y-1">
          {PHASE_ORDER.map((phase, index) => {
            const Icon = PHASE_ICONS[phase] ?? Loader2;
            const isDone = currentIndex > index || currentPhase === 'COMPLETED';
            const isActive = currentPhase === phase;
            return (
              <li
                key={phase}
                className={cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all',
                  isActive && 'bg-primary/10',
                  isDone && !isActive && 'opacity-60'
                )}
              >
                <span
                  className={cn(
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                    isDone ? 'bg-emerald-500/15 text-emerald-600' : isActive ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground'
                  )}
                >
                  <Icon className={cn('h-4 w-4', isActive && !isDone && 'animate-spin')} />
                </span>
                <span
                  className={cn(
                    'text-xs font-bold',
                    isActive ? 'text-foreground' : isDone ? 'text-muted-foreground line-through' : 'text-muted-foreground'
                  )}
                >
                  {PHASE_LABELS[phase]}
                </span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
