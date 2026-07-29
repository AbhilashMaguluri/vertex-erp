/**
 * The counsellor's workspace — the landing page for a COUNSELLOR role.
 *
 * This is a workspace, not a report. Every screenful is arranged to answer, in
 * order: who needs me right now, what do I owe today, and how fast can I reach
 * a student's record or log a session. Statistics are present but subordinate —
 * they sit below the worklists and suppress themselves entirely when there is
 * nothing to plot.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { counsellingService, CounsellorDashboard as DashboardData } from '@/features/counselling/services/counselling.service';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { cn } from '@/shared/utils/cn';
import {
  PriorityStudents,
  TodaysTasks,
  FollowUpTracker,
  TodaysAgenda,
  RecentActivity,
} from './WorkspacePanels';
import { CaseloadAnalytics } from './CaseloadAnalytics';
import {
  AlertTriangle,
  BookX,
  CalendarCheck,
  ClipboardList,
  Download,
  FolderOpen,
  GraduationCap,
  MessageSquare,
  MessageSquarePlus,
  Search,
  ShieldAlert,
  TrendingDown,
  Users,
} from 'lucide-react';

export function CounsellorDashboard() {
  const { user } = useAuth();
  const firstName = user?.full_name?.split(' ')[0] ?? 'there';

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['counselling', 'dashboard'],
    queryFn: counsellingService.getDashboard,
  });

  if (isLoading) return <WorkspaceSkeleton />;

  if (isError || !data) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Could not load your workspace"
        description="Something went wrong fetching your caseload. Your students are unaffected — this is a display problem."
        actionLabel="Retry"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-5">
      <WorkspaceHeader firstName={firstName} data={data} />

      <KpiRow data={data} />

      {/* Priority work sits highest and widest: 8 of 12 columns for the
          students needing attention, 4 for what is due today. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <PriorityStudents
            students={data.students_needing_attention}
            totalStudents={data.total_students}
          />
        </div>
        <div className="space-y-4 lg:col-span-4">
          <TodaysTasks followUps={data.upcoming_follow_ups} />
          <RiskCentre data={data} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <FollowUpTracker followUps={data.upcoming_follow_ups} />
        <TodaysAgenda agenda={data.agenda_today} />
        <RecentActivity activity={data.recent_activity} />
      </div>

      <div className="space-y-3">
        <h2 className="text-xs font-extrabold uppercase tracking-widest text-muted-foreground">
          Caseload analytics
        </h2>
        <CaseloadAnalytics data={data} />
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Compact header                                                             */
/* -------------------------------------------------------------------------- */

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

/** One compact strip in place of the old hero banner: who you are, the five
 *  numbers that decide what you do next, and the four actions you take most.
 *  Deliberately no illustration, no gradient panel and no paragraph of prose —
 *  that space belongs to the worklists below. */
function WorkspaceHeader({ firstName, data }: { firstName: string; data: DashboardData }) {
  const { hasPermission } = useAuth();

  const metrics: { label: string; value: string | number; alert?: boolean }[] = [
    { label: 'Assigned students', value: data.total_students },
    {
      label: 'Pending follow-ups',
      value: data.follow_ups_pending,
      alert: data.follow_ups_overdue > 0,
    },
    { label: "Today's sessions", value: data.sessions_today },
    { label: 'High risk', value: data.risk_high, alert: data.risk_high > 0 },
    { label: 'Overdue', value: data.follow_ups_overdue, alert: data.follow_ups_overdue > 0 },
  ];

  const actions = [
    {
      label: 'Record session',
      to: '/counselling/new',
      icon: MessageSquarePlus,
      permission: 'counselling.create',
      primary: true,
    },
    { label: 'Assigned students', to: '/students', icon: Users, permission: 'student.caseload.read' },
    {
      label: 'Search student',
      to: '/students?focus=search',
      icon: Search,
      permission: 'student.caseload.read',
    },
    { label: 'Export report', to: '/reports', icon: Download, permission: 'report.generate' },
  ].filter((a) => hasPermission(a.permission));

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border/80 bg-card p-4 shadow-xs xl:flex-row xl:items-center xl:justify-between">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-6">
        <div className="shrink-0">
          <h1 className="text-lg font-black tracking-tight text-foreground">
            {greeting()}, {firstName}
          </h1>
          <p className="text-[11px] text-muted-foreground">
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </p>
        </div>

        <div className="hidden h-10 w-px shrink-0 bg-border/80 lg:block" />

        <dl className="flex flex-wrap items-center gap-x-5 gap-y-2">
          {metrics.map((m) => (
            <div key={m.label}>
              <dt className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                {m.label}
              </dt>
              <dd
                className={cn(
                  'text-lg font-black leading-tight',
                  m.alert ? 'text-rose-600 dark:text-rose-400' : 'text-foreground'
                )}
              >
                {m.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="flex flex-wrap items-center gap-2 xl:shrink-0">
        {actions.map((a) => (
          <Button
            key={a.to}
            asChild
            size="sm"
            variant={a.primary ? 'default' : 'outline'}
            className="font-bold"
          >
            <Link to={a.to}>
              <a.icon className="mr-1.5 h-3.5 w-3.5" />
              {a.label}
            </Link>
          </Button>
        ))}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* KPI row                                                                    */
/* -------------------------------------------------------------------------- */

/** Compact, and every one is a link. A KPI a counsellor cannot click through
 *  to the underlying students is a poster, not a control. */
function KpiCard({
  label,
  value,
  caption,
  icon: Icon,
  to,
  alert,
}: {
  label: string;
  value: string | number;
  caption: string;
  icon: React.ElementType;
  to: string;
  alert?: boolean;
}) {
  return (
    <Link
      to={to}
      className="group flex flex-col justify-between rounded-xl border border-border/80 bg-card p-3.5 shadow-xs transition-all hover:border-primary/50 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[10px] font-extrabold uppercase leading-tight tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon
          className={cn(
            'h-3.5 w-3.5 shrink-0 transition-transform group-hover:scale-110',
            alert ? 'text-rose-500' : 'text-primary'
          )}
        />
      </div>
      <div
        className={cn(
          'mt-2 text-2xl font-black tracking-tight',
          alert ? 'text-rose-600 dark:text-rose-400' : 'text-foreground'
        )}
      >
        {value}
      </div>
      <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{caption}</p>
    </Link>
  );
}

function KpiRow({ data }: { data: DashboardData }) {
  const attendance = data.average_attendance;
  const cgpa = data.average_cgpa;

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
      <KpiCard
        label="Assigned"
        value={data.total_students}
        caption="Students in your caseload"
        icon={Users}
        to="/students"
      />
      <KpiCard
        label="Active cases"
        value={data.active_cases}
        caption="With open follow-ups"
        icon={FolderOpen}
        to="/counselling/sessions"
      />
      <KpiCard
        label="Sessions today"
        value={data.sessions_today}
        caption={`${data.sessions_this_month} this month`}
        icon={MessageSquare}
        to="/counselling/sessions"
      />
      <KpiCard
        label="Follow-ups"
        value={data.follow_ups_pending}
        caption={data.follow_ups_overdue > 0 ? `${data.follow_ups_overdue} overdue` : 'None overdue'}
        icon={ClipboardList}
        to="/counselling/sessions"
        alert={data.follow_ups_overdue > 0}
      />
      <KpiCard
        label="Avg attendance"
        value={attendance != null ? `${attendance}%` : '—'}
        caption={
          attendance == null
            ? 'Not recorded yet'
            : attendance >= 75
              ? 'Above 75% threshold'
              : 'Below 75% threshold'
        }
        icon={CalendarCheck}
        to="/students?sort_by=attendance&sort_dir=asc"
        alert={attendance != null && attendance < 75}
      />
      <KpiCard
        label="Avg CGPA"
        value={cgpa != null ? cgpa.toFixed(2) : '—'}
        caption={cgpa == null ? 'No results published' : 'Across your caseload'}
        icon={GraduationCap}
        to="/students?sort_by=cgpa&sort_dir=asc"
      />
      <KpiCard
        label="High risk"
        value={data.risk_high}
        caption="High or critical"
        icon={ShieldAlert}
        to="/students?risk_level=HIGH"
        alert={data.risk_high > 0}
      />
      <KpiCard
        label="With backlogs"
        value={data.with_backlogs_count}
        caption="Carrying active backlogs"
        icon={BookX}
        to="/students?has_backlogs=true"
        alert={data.with_backlogs_count > 0}
      />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Risk centre                                                                */
/* -------------------------------------------------------------------------- */

/** Status tiers, each carrying an icon and its tier name — the count is never
 *  distinguished by colour alone. Clicking a tier filters Assigned Students. */
function RiskCentre({ data }: { data: DashboardData }) {
  const tiers = [
    {
      label: 'High risk',
      value: data.risk_high,
      to: '/students?risk_level=HIGH',
      icon: ShieldAlert,
      tone: 'border-rose-500/25 bg-rose-500/5 text-rose-600 dark:text-rose-400',
    },
    {
      label: 'Medium risk',
      value: data.risk_medium,
      to: '/students?risk_level=MEDIUM',
      icon: AlertTriangle,
      tone: 'border-amber-500/25 bg-amber-500/5 text-amber-600 dark:text-amber-400',
    },
    {
      label: 'Low / none',
      value: data.risk_low,
      to: '/students?risk_level=LOW',
      icon: CalendarCheck,
      tone: 'border-emerald-500/25 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400',
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Risk centre</CardTitle>
        <CardDescription>Select a tier to filter your assigned students</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {tiers.map((t) => (
          <Link
            key={t.label}
            to={t.to}
            className={cn(
              'flex items-center justify-between gap-3 rounded-xl border p-3 transition-all hover:shadow-md',
              t.tone
            )}
          >
            <span className="flex items-center gap-2">
              <t.icon className="h-4 w-4 shrink-0" />
              <span className="text-xs font-bold text-foreground">{t.label}</span>
            </span>
            <span className="text-xl font-black text-foreground">{t.value}</span>
          </Link>
        ))}

        {/* The two non-risk cohorts a counsellor chases just as often. */}
        <div className="grid grid-cols-2 gap-2 border-t border-border/60 pt-2">
          <Link
            to="/students?max_attendance=74.9"
            className="rounded-xl border border-border/70 bg-muted/20 p-2.5 transition-colors hover:bg-accent"
          >
            <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              <TrendingDown className="h-3 w-3" /> Below 75%
            </span>
            <span className="mt-0.5 block text-lg font-black text-foreground">
              {data.below_attendance_count}
            </span>
          </Link>
          <Link
            to="/students?has_backlogs=true"
            className="rounded-xl border border-border/70 bg-muted/20 p-2.5 transition-colors hover:bg-accent"
          >
            <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              <BookX className="h-3 w-3" /> Backlogs
            </span>
            <span className="mt-0.5 block text-lg font-black text-foreground">
              {data.with_backlogs_count}
            </span>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */

function WorkspaceSkeleton() {
  return (
    <div className="space-y-5">
      <Skeleton className="h-24 rounded-2xl" />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Skeleton className="h-96 rounded-2xl lg:col-span-8" />
        <Skeleton className="h-96 rounded-2xl lg:col-span-4" />
      </div>
    </div>
  );
}
