/**
 * Shared presentation primitives for student data.
 *
 * The caseload table, the counsellor dashboard and the 360 workspace all
 * render the same concepts (risk tier, attendance health, "no data yet"), so
 * the colour and wording rules live here once. Anything that renders a
 * student metric should use these rather than re-deriving thresholds.
 */
import { Badge } from '@/shared/components/ui/Badge';
import { cn } from '@/shared/utils/cn';

/** Institutional minimum attendance. Mirrors ATTENDANCE_THRESHOLD in the
 *  backend's students service — the API is authoritative and already sends
 *  `attendance_below_threshold`; this is only for local styling decisions. */
export const ATTENDANCE_THRESHOLD = 75;

export type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info';

export function riskVariant(level: string): BadgeVariant {
  switch (level) {
    case 'CRITICAL':
    case 'HIGH':
      return 'destructive';
    case 'MEDIUM':
      return 'warning';
    case 'LOW':
      return 'info';
    default:
      return 'secondary';
  }
}

export function RiskBadge({ level, className }: { level: string; className?: string }) {
  return (
    <Badge variant={riskVariant(level)} className={className} dot={level === 'HIGH' || level === 'CRITICAL'}>
      {level}
    </Badge>
  );
}

/** Renders "—" for absent data rather than 0, so an un-imported student is
 *  never mistaken for a student with zero attendance. */
export function AttendanceCell({ value }: { value?: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground/60">No data</span>;
  }
  const low = value < ATTENDANCE_THRESHOLD;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-14 shrink-0 overflow-hidden rounded-full bg-muted/70">
        <div
          className={cn('h-full rounded-full', low ? 'bg-rose-500' : 'bg-emerald-500')}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <span className={cn('font-bold tabular-nums', low ? 'text-rose-600 dark:text-rose-400' : 'text-foreground')}>
        {value}%
      </span>
    </div>
  );
}

export function GpaCell({ value }: { value?: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground/60">No data</span>;
  }
  return <span className="font-bold tabular-nums text-foreground">{value.toFixed(2)}</span>;
}

export function StudentAvatar({
  name,
  photoUrl,
  size = 'md',
}: {
  name: string;
  photoUrl?: string | null;
  size?: 'sm' | 'md' | 'lg';
}) {
  const dims = {
    sm: 'h-8 w-8 text-[10px] rounded-lg',
    md: 'h-10 w-10 text-xs rounded-xl',
    lg: 'h-16 w-16 text-2xl rounded-2xl',
  }[size];

  const initials = name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase();

  if (photoUrl) {
    return <img src={photoUrl} alt={name} className={cn(dims, 'shrink-0 object-cover ring-1 ring-border/70')} />;
  }

  return (
    <div
      className={cn(
        dims,
        'flex shrink-0 items-center justify-center bg-gradient-to-tr from-brand-500 to-brand-600 font-black text-white shadow-sm'
      )}
    >
      {initials || '?'}
    </div>
  );
}

export function formatDate(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

/** "Never" reads better than "—" for a counselling date: it is a meaningful
 *  state (this student has never been seen), not missing data. */
export function formatSessionDate(value?: string | null): string {
  return value ? formatDate(value) : 'Never';
}

export function yearLabel(year?: number | null): string {
  if (!year) return '—';
  return ['1st', '2nd', '3rd', '4th'][year - 1] ?? `${year}`;
}
