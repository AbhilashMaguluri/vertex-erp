/**
 * The worklist panels of the counsellor workspace.
 *
 * Every panel here answers one of the three questions the workspace exists to
 * answer: who needs me now, what do I owe today, and what have I just done.
 * They are deliberately action-first — each row carries the buttons that let a
 * counsellor act without navigating away and coming back.
 */
import * as React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  counsellingService,
  AttentionStudent,
  AttentionFlag,
  UpcomingFollowUp,
  ActivityEntry,
  AgendaEntry,
} from '@/features/counselling/services/counselling.service';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { RiskBadge, StudentAvatar, formatDate, yearLabel } from '@/features/students/components/StudentPresentation';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { cn } from '@/shared/utils/cn';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  CircleAlert,
  ClipboardList,
  Clock,
  ExternalLink,
  History,
  Mail,
  MessageSquarePlus,
  Phone,
  Users,
  CalendarDays,
  Undo2,
} from 'lucide-react';

/* -------------------------------------------------------------------------- */
/* Shared helpers                                                             */
/* -------------------------------------------------------------------------- */

/** Status tone tokens. Reserved for state — never reused as a series colour.
 *  Each is always rendered alongside an icon and a text label, so the state is
 *  never carried by colour alone. */
const TONES = {
  critical: 'border-rose-500/25 bg-rose-500/5 text-rose-600 dark:text-rose-400',
  serious: 'border-orange-500/25 bg-orange-500/5 text-orange-600 dark:text-orange-400',
  warning: 'border-amber-500/25 bg-amber-500/5 text-amber-600 dark:text-amber-400',
  good: 'border-emerald-500/25 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400',
  neutral: 'border-border/70 bg-muted/20 text-muted-foreground',
} as const;

/** Ink-only variants, for tone applied to bare text rather than a chip. Kept as
 *  whole literals so Tailwind can see every class it must generate. */
const TEXT_TONES = {
  critical: 'text-rose-600 dark:text-rose-400',
  serious: 'text-orange-600 dark:text-orange-400',
  warning: 'text-amber-600 dark:text-amber-400',
  good: 'text-emerald-600 dark:text-emerald-400',
  neutral: 'text-muted-foreground',
} as const;

type Tone = keyof typeof TONES;

/** The attention triggers, in the order a counsellor should read them. Label
 *  and icon travel with the tone so no row is colour-only. */
const FLAG_META: Record<AttentionFlag, { label: string; tone: Tone }> = {
  LOW_ATTENDANCE: { label: 'Attendance below 75%', tone: 'critical' },
  MANY_BACKLOGS: { label: 'More than 3 backlogs', tone: 'critical' },
  HIGH_RISK: { label: 'High risk', tone: 'serious' },
  BACKLOGS: { label: 'Carrying backlogs', tone: 'warning' },
  NEVER_COUNSELLED: { label: 'Never counselled', tone: 'warning' },
};

const FLAG_ORDER: AttentionFlag[] = [
  'LOW_ATTENDANCE',
  'MANY_BACKLOGS',
  'HIGH_RISK',
  'BACKLOGS',
  'NEVER_COUNSELLED',
];

function FlagChip({ flag }: { flag: AttentionFlag }) {
  const meta = FLAG_META[flag];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold',
        TONES[meta.tone]
      )}
    >
      <CircleAlert className="h-2.5 w-2.5" />
      {meta.label}
    </span>
  );
}

/** Today / Yesterday / an actual date. Dates are compared on the local
 *  calendar day, not by subtracting timestamps, so a session recorded at
 *  23:50 doesn't read as "yesterday" the moment the clock rolls over. */
function relativeDay(value: string): 'Today' | 'Yesterday' | string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diffDays = Math.round((startOf(new Date()) - startOf(d)) / 86_400_000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays > 1 && diffDays <= 7) return 'Last week';
  return formatDate(value);
}

function dueLabel(dueDate: string, isOverdue: boolean): { text: string; tone: Tone } {
  if (isOverdue) return { text: `Overdue — was due ${formatDate(dueDate)}`, tone: 'critical' };
  const rel = relativeDay(dueDate);
  if (rel === 'Today') return { text: 'Due today', tone: 'serious' };
  const d = new Date(dueDate);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (d.toDateString() === tomorrow.toDateString()) return { text: 'Due tomorrow', tone: 'warning' };
  return { text: `Due ${formatDate(dueDate)}`, tone: 'neutral' };
}

/** Shared invalidation for anything that mutates a follow-up: the dashboard
 *  counters, the caseload's "next follow-up" column and the student's own
 *  counselling history all go stale together. */
function useFollowUpMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...changes }: { id: string; status?: string; due_date?: string }) =>
      counsellingService.updateFollowUp(id, changes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counselling'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
  });
}

function PanelEmpty({
  icon: Icon,
  title,
  hint,
}: {
  icon: React.ElementType;
  title: string;
  hint: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed border-border/70 px-4 py-8 text-center">
      <Icon className="h-5 w-5 text-muted-foreground/50" />
      <p className="text-xs font-bold text-foreground">{title}</p>
      <p className="max-w-xs text-[11px] leading-relaxed text-muted-foreground">{hint}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* 1. Priority students — the largest panel on the dashboard                  */
/* -------------------------------------------------------------------------- */

export function PriorityStudents({
  students,
  totalStudents,
}: {
  students: AttentionStudent[];
  totalStudents: number;
}) {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canCreateSession = hasPermission('counselling.create');

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-rose-500" />
            Students needing immediate attention
          </CardTitle>
          <CardDescription>
            Ranked by risk, then attendance and backlogs — work down from the top
          </CardDescription>
        </div>
        <Button asChild size="sm" variant="outline" className="shrink-0">
          <Link to="/students">
            All students <ExternalLink className="ml-1 h-3 w-3" />
          </Link>
        </Button>
      </CardHeader>

      <CardContent className="flex-1 space-y-2">
        {students.length === 0 ? (
          totalStudents === 0 ? (
            <PanelEmpty
              icon={Users}
              title="No students assigned yet"
              hint="Ask your administrator to assign students to you by year, section or branch. Once assigned, the ones needing attention appear here first."
            />
          ) : (
            <PanelEmpty
              icon={CheckCircle2}
              title="Nobody is flagged right now"
              hint={`None of your ${totalStudents} students is currently below 75% attendance, carrying backlogs, or flagged high risk.`}
            />
          )
        ) : (
          students.map((s) => {
            const flags = FLAG_ORDER.filter((f) => s.flags.includes(f));
            return (
              <div
                key={s.id}
                className="flex flex-col gap-3 rounded-xl border border-border/70 bg-muted/20 p-3 transition-colors hover:bg-accent/40 lg:flex-row lg:items-center lg:justify-between"
              >
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <StudentAvatar name={s.full_name} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/students/${s.id}`}
                        className="truncate text-xs font-bold text-foreground hover:text-primary hover:underline"
                      >
                        {s.full_name}
                      </Link>
                      <RiskBadge level={s.risk_level} />
                    </div>
                    <div className="truncate font-mono text-[11px] text-muted-foreground">
                      {s.roll_number}
                      {s.section_name ? ` • Sec ${s.section_name}` : ''}
                      {s.study_year ? ` • ${yearLabel(s.study_year)} Yr` : ''}
                      {' • last seen '}
                      {s.last_session_date ? formatDate(s.last_session_date) : 'never'}
                    </div>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {flags.map((f) => (
                        <FlagChip key={f} flag={f} />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-1.5 self-end lg:self-center">
                  <Button size="sm" variant="outline" onClick={() => navigate(`/students/${s.id}`)}>
                    <ExternalLink className="mr-1.5 h-3.5 w-3.5" /> Profile
                  </Button>
                  {canCreateSession && (
                    <Button size="sm" onClick={() => navigate(`/counselling/new?studentId=${s.id}`)}>
                      <MessageSquarePlus className="mr-1.5 h-3.5 w-3.5" /> Session
                    </Button>
                  )}
                  <ContactButtons email={s.email} phone={s.phone} name={s.full_name} />
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

/** There is no in-app messaging service in this system, so "send a message"
 *  hands off to the device's mail/dialer with the contact details already on
 *  the student record rather than pretending to deliver something. */
function ContactButtons({
  email,
  phone,
  name,
}: {
  email?: string | null;
  phone?: string | null;
  name: string;
}) {
  if (!email && !phone) {
    return (
      <Button size="sm" variant="outline" disabled title={`No contact details on file for ${name}`}>
        <Mail className="h-3.5 w-3.5" />
      </Button>
    );
  }
  return (
    <>
      {email && (
        <Button asChild size="sm" variant="outline" title={`Email ${email}`}>
          <a href={`mailto:${email}`}>
            <Mail className="h-3.5 w-3.5" />
          </a>
        </Button>
      )}
      {phone && (
        <Button asChild size="sm" variant="outline" title={`Call ${phone}`}>
          <a href={`tel:${phone}`}>
            <Phone className="h-3.5 w-3.5" />
          </a>
        </Button>
      )}
    </>
  );
}

/* -------------------------------------------------------------------------- */
/* 2. Today's tasks                                                           */
/* -------------------------------------------------------------------------- */

/** Checkable work for today. These are real action items agreed in a previous
 *  session — ticking one PATCHes it to COMPLETED, it is not local UI state. */
export function TodaysTasks({ followUps }: { followUps: UpcomingFollowUp[] }) {
  const { hasPermission } = useAuth();
  const canUpdate = hasPermission('counselling.update');
  const mutation = useFollowUpMutation();

  const due = followUps.filter((f) => f.is_overdue || f.is_due_today);
  const overdueCount = due.filter((f) => f.is_overdue).length;

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <ClipboardList className="h-4 w-4 text-primary" />
            Today's tasks
          </CardTitle>
          <CardDescription>Commitments that have come due</CardDescription>
        </div>
        {overdueCount > 0 && (
          <Badge variant="destructive" className="shrink-0">
            {overdueCount} overdue
          </Badge>
        )}
      </CardHeader>

      <CardContent className="flex-1 space-y-2">
        {due.length === 0 ? (
          <PanelEmpty
            icon={CheckCircle2}
            title="Nothing due today"
            hint="Action items you agree with a student during a session land here on their due date."
          />
        ) : (
          due.map((f) => {
            const label = dueLabel(f.due_date, f.is_overdue);
            const isPending = mutation.isPending && mutation.variables?.id === f.id;
            return (
              <div
                key={f.id}
                className="flex items-start gap-2.5 rounded-xl border border-border/70 bg-muted/20 p-3"
              >
                <button
                  type="button"
                  disabled={!canUpdate || isPending}
                  onClick={() => mutation.mutate({ id: f.id, status: 'COMPLETED' })}
                  title={canUpdate ? 'Mark complete' : 'You do not have permission to close follow-ups'}
                  className={cn(
                    'mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 border-muted-foreground/40 transition-colors',
                    canUpdate && 'cursor-pointer hover:border-emerald-500 hover:bg-emerald-500/10',
                    !canUpdate && 'cursor-not-allowed opacity-50',
                    isPending && 'animate-pulse border-emerald-500'
                  )}
                >
                  {isPending && <CheckCircle2 className="h-3 w-3 text-emerald-500" />}
                </button>

                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold leading-snug text-foreground">{f.description}</p>
                  <Link
                    to={`/students/${f.student_id}?tab=counselling`}
                    className="font-mono text-[11px] text-muted-foreground hover:text-primary hover:underline"
                  >
                    {f.student_name} • {f.student_roll_number}
                  </Link>
                  <div className={cn('mt-1 text-[10px] font-bold', TEXT_TONES[label.tone])}>
                    {label.text}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* 3. Follow-up tracker                                                       */
/* -------------------------------------------------------------------------- */

export function FollowUpTracker({ followUps }: { followUps: UpcomingFollowUp[] }) {
  const { hasPermission } = useAuth();
  const canUpdate = hasPermission('counselling.update');
  const mutation = useFollowUpMutation();
  const [reschedulingId, setReschedulingId] = React.useState<string | null>(null);

  // The API rejects a past due date, so the picker cannot offer one.
  const todayIso = new Date().toISOString().split('T')[0];

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CalendarClock className="h-4 w-4 text-primary" />
          Pending follow-ups
        </CardTitle>
        <CardDescription>Complete or reschedule without leaving this page</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-2">
        {followUps.length === 0 ? (
          <PanelEmpty
            icon={CheckCircle2}
            title="No open follow-ups"
            hint="Every action item you have set is closed. New ones appear here as you add them to sessions."
          />
        ) : (
          followUps.slice(0, 8).map((f) => {
            const label = dueLabel(f.due_date, f.is_overdue);
            const isPending = mutation.isPending && mutation.variables?.id === f.id;
            return (
              <div key={f.id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <Link
                      to={`/students/${f.student_id}?tab=counselling`}
                      className="truncate text-xs font-bold text-foreground hover:text-primary hover:underline"
                    >
                      {f.student_name}
                    </Link>
                    <p className="line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
                      {f.description}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-bold',
                      TONES[label.tone]
                    )}
                  >
                    {label.text}
                  </span>
                </div>

                {canUpdate && (
                  <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/60 pt-2.5">
                    <Button
                      size="sm"
                      variant="outline"
                      isLoading={isPending && mutation.variables?.status === 'COMPLETED'}
                      onClick={() => mutation.mutate({ id: f.id, status: 'COMPLETED' })}
                    >
                      <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Complete
                    </Button>

                    {reschedulingId === f.id ? (
                      <span className="flex items-center gap-1.5">
                        <input
                          type="date"
                          min={todayIso}
                          defaultValue={f.due_date}
                          autoFocus
                          onChange={(e) => {
                            if (!e.target.value) return;
                            mutation.mutate({ id: f.id, due_date: e.target.value });
                            setReschedulingId(null);
                          }}
                          className="h-8 rounded-lg border border-input bg-background px-2 text-[11px] font-semibold focus:ring-2 focus:ring-ring"
                        />
                        <Button size="sm" variant="ghost" onClick={() => setReschedulingId(null)}>
                          <Undo2 className="h-3.5 w-3.5" />
                        </Button>
                      </span>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => setReschedulingId(f.id)}>
                        <CalendarDays className="mr-1.5 h-3.5 w-3.5" /> Reschedule
                      </Button>
                    )}

                    <Button asChild size="sm" variant="ghost">
                      <Link to={`/students/${f.student_id}`}>View student</Link>
                    </Button>
                  </div>
                )}
              </div>
            );
          })
        )}

        {mutation.isError && (
          <p className="text-[11px] font-semibold text-destructive">
            Could not update that follow-up. Please retry.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* 4. Today's agenda                                                          */
/* -------------------------------------------------------------------------- */

/** No clock times appear here on purpose. Sessions store a `session_date` and
 *  action items a `due_date` — both plain dates — so this system has no notion
 *  of what time anything happens. Items are ordered by urgency instead, and a
 *  footnote says so rather than inventing "10:00". */
export function TodaysAgenda({ agenda }: { agenda: AgendaEntry[] }) {
  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CalendarDays className="h-4 w-4 text-primary" />
          Today's schedule
        </CardTitle>
        <CardDescription>{today}</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-2">
        {agenda.length === 0 ? (
          <PanelEmpty
            icon={CalendarDays}
            title="Nothing scheduled for today"
            hint="Follow-ups that fall due and sessions you record today show up here."
          />
        ) : (
          <>
            {agenda.map((a) => (
              <Link
                key={`${a.kind}-${a.reference_id}`}
                to={
                  a.kind === 'SESSION'
                    ? `/students/${a.student_id}?tab=counselling`
                    : `/students/${a.student_id}`
                }
                className="flex items-start gap-3 rounded-xl border border-border/70 bg-muted/20 p-3 transition-colors hover:bg-accent/40"
              >
                <span
                  className={cn(
                    'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border',
                    a.kind === 'SESSION'
                      ? TONES.good
                      : a.is_overdue
                        ? TONES.critical
                        : TONES.serious
                  )}
                >
                  {a.kind === 'SESSION' ? (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  ) : (
                    <Clock className="h-3.5 w-3.5" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-xs font-bold text-foreground">{a.student_name}</div>
                  <div className="truncate text-[11px] text-muted-foreground">{a.label}</div>
                  <div className="font-mono text-[10px] text-muted-foreground/70">
                    {a.student_roll_number}
                    {a.kind === 'FOLLOW_UP' && a.is_overdue ? ' • carried over' : ''}
                  </div>
                </div>
              </Link>
            ))}
            <p className="pt-1 text-[10px] leading-relaxed text-muted-foreground/70">
              Ordered by urgency. Sessions and follow-ups are recorded against a date, not a
              time of day, so no appointment times are shown.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* 5. Recent activity                                                         */
/* -------------------------------------------------------------------------- */

export function RecentActivity({ activity }: { activity: ActivityEntry[] }) {
  // Group into the buckets a counsellor thinks in, preserving server order
  // (most recent first) within each.
  const groups = React.useMemo(() => {
    const out = new Map<string, ActivityEntry[]>();
    activity.forEach((a) => {
      const key = relativeDay(a.session_date);
      const bucket = out.get(key) ?? [];
      bucket.push(a);
      out.set(key, bucket);
    });
    return Array.from(out.entries());
  }, [activity]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4 text-primary" />
          Recent counselling activity
        </CardTitle>
        <CardDescription>Sessions you have recorded</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {activity.length === 0 ? (
          <PanelEmpty
            icon={MessageSquarePlus}
            title="No sessions recorded yet"
            hint="Record your first counselling session and it will appear here, newest first."
          />
        ) : (
          groups.map(([label, entries]) => (
            <div key={label} className="space-y-2">
              <div className="text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">
                {label}
              </div>
              {entries.map((a) => (
                <Link
                  key={a.session_id}
                  to={`/students/${a.student_id}?tab=counselling`}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border/70 bg-muted/20 p-3 transition-colors hover:bg-accent/40"
                >
                  <div className="min-w-0">
                    <div className="truncate text-xs font-bold text-foreground">{a.student_name}</div>
                    <div className="truncate font-mono text-[11px] text-muted-foreground">
                      {a.student_roll_number} • {a.mode.replace('_', ' ').toLowerCase()}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    {a.follow_up_required && (
                      <Badge variant="secondary" className="text-[9px]">
                        Follow-up
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-[9px]">
                      {a.session_type}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
