/**
 * Student 360 tabs backed by student-maintained profile data.
 *
 * These render what students enter in their own portal. For staff they are
 * strictly read-only: the API exposes no counsellor-writable route for
 * personal, family, contact or skills data (see profile_router.py), so there
 * is deliberately no edit affordance here either.
 */
import { useQuery } from '@tanstack/react-query';
import { profileService } from '../services/profile.service';
import { counsellingService } from '@/features/counselling/services/counselling.service';
import { attendanceService } from '@/features/attendance/services/attendance.service';
import { academicsService } from '@/features/academics/services/academics.service';
import { PersonalDetailsTab } from './PersonalDetailsTab';
import { RiskBadge, formatDate } from './StudentPresentation';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { cn } from '@/shared/utils/cn';
import { AlertTriangle, CheckCircle2, Contact, ListChecks, Target } from 'lucide-react';

type Mode = 'staff' | 'self';

function TabSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-24 w-full rounded-xl" />
      <Skeleton className="h-48 w-full rounded-xl" />
    </div>
  );
}

function TabError({ message }: { message: string }) {
  return <EmptyState icon={AlertTriangle} title="Something went wrong" description={message} />;
}

/** Staff read the profile via /students/:id/profile (scoped to assigned
 *  students); the student reads their own via /students/me/profile. */
function useStudentProfile(studentId: string, mode: Mode) {
  return useQuery({
    queryKey: mode === 'staff' ? ['students', studentId, 'profile'] : ['profile', 'me'],
    queryFn: () =>
      mode === 'staff' ? profileService.getStudentProfile(studentId) : profileService.getMyProfile(),
  });
}

export function ProfileTab({ studentId, mode }: { studentId: string; mode: Mode }) {
  const { data, isLoading, isError } = useStudentProfile(studentId, mode);

  if (isLoading) return <TabSkeleton />;
  if (isError || !data) return <TabError message="Could not load this student's profile details." />;

  const nothingFilled =
    !data.mobile_number && !data.father_name && !data.mother_name && !data.permanent_address;

  if (nothingFilled) {
    return (
      <EmptyState
        icon={Contact}
        title="Profile not filled in yet"
        description={
          mode === 'staff'
            ? `This student has not completed their personal, family or contact details — their profile is ${data.completion.percentage}% complete.`
            : 'Head to My Profile to add your personal, family and contact details.'
        }
      />
    );
  }

  return <PersonalDetailsTab profile={data} isStudentMode={mode === 'self'} />;
}

export function SkillsGoalsTab({ studentId, mode }: { studentId: string; mode: Mode }) {
  const { data, isLoading, isError } = useStudentProfile(studentId, mode);

  if (isLoading) return <TabSkeleton />;
  if (isError || !data) return <TabError message="Could not load skills and goals." />;

  const tagGroups: [string, string[] | null | undefined][] = [
    ['Technical skills', data.technical_skills],
    ['Programming languages', data.programming_languages],
    ['Soft skills', data.soft_skills],
    ['Interests', data.interests],
    ['Hobbies', data.hobbies],
  ];
  const textGroups: [string, string | null | undefined][] = [
    ['Career goal', data.career_goal],
    ['Higher studies goal', data.higher_studies_goal],
    ['Dream company', data.dream_company],
    ['Strengths', data.strengths],
    ['Weaknesses', data.weaknesses],
    ['Areas needing improvement', data.areas_to_improve],
  ];
  const links: [string, string | null | undefined][] = [
    ['Resume', data.resume_url],
    ['LinkedIn', data.linkedin_url],
    ['GitHub', data.github_url],
    ['Portfolio', data.portfolio_url],
    ['LeetCode', data.leetcode_url],
    ['CodeChef', data.codechef_url],
    ['HackerRank', data.hackerrank_url],
  ];

  const nothing =
    tagGroups.every(([, v]) => !v?.length) &&
    textGroups.every(([, v]) => !v) &&
    links.every(([, v]) => !v);

  if (nothing) {
    return (
      <EmptyState
        icon={Target}
        title="No skills or goals recorded"
        description={
          mode === 'staff'
            ? 'This student has not filled in their skills, goals or portfolio links — a useful thing to raise in a session.'
            : 'Add your skills and career goals so your counsellor can guide you better.'
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Skills</CardTitle>
          <CardDescription>Self-reported by the student</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {tagGroups.map(([label, values]) => (
            <div key={label} className="space-y-1.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                {label}
              </div>
              {values?.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {values.map((v) => (
                    <Badge key={v} variant="secondary">
                      {v}
                    </Badge>
                  ))}
                </div>
              ) : (
                <span className="text-xs italic text-muted-foreground/50">Not provided</span>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Goals &amp; self-assessment</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {textGroups.map(([label, value]) => (
            <div key={label} className="space-y-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                {label}
              </div>
              <div className={cn('text-xs', value ? 'text-foreground' : 'italic text-muted-foreground/50')}>
                {value || 'Not provided'}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {links.filter(([, url]) => url).length === 0 && (
              <span className="text-xs italic text-muted-foreground/50">No links added</span>
            )}
            {links
              .filter(([, url]) => url)
              .map(([label, url]) => (
                <a
                  key={label}
                  href={url as string}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1 text-[11px] font-bold text-foreground transition-colors hover:bg-accent"
                >
                  {label}
                </a>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/** Every action item across all of this student's sessions, so a counsellor
 *  can see what was promised without opening each session in turn. */
export function ActionItemsTab({ studentId, mode }: { studentId: string; mode: Mode }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['counselling', 'sessions', studentId, mode, 'actions'],
    queryFn: () =>
      mode === 'self' ? counsellingService.getMySessions() : counsellingService.getSessions(studentId),
  });

  if (isLoading) return <TabSkeleton />;
  if (isError || !data) return <TabError message="Could not load action items." />;

  const today = new Date().toISOString().split('T')[0];
  const items = data.flatMap((session) =>
    (session.action_items ?? []).map((item) => ({
      ...item,
      sessionDate: session.session_date,
      sessionType: session.session_type,
    }))
  );

  if (items.length === 0) {
    return (
      <EmptyState
        icon={ListChecks}
        title="No action items"
        description="Action items agreed during counselling sessions appear here."
      />
    );
  }

  const open = items.filter((i) => i.status !== 'COMPLETED');
  const done = items.filter((i) => i.status === 'COMPLETED');

  const Row = ({ item }: { item: (typeof items)[number] }) => {
    // Overdue is derived from the due date, not the stored status — nothing
    // sweeps PENDING rows to OVERDUE, so the stored value goes stale.
    const overdue = item.status !== 'COMPLETED' && item.due_date < today;
    return (
      <div className="flex items-start justify-between gap-3 rounded-xl border border-border/70 bg-muted/20 p-3">
        <div className="min-w-0">
          <div className="text-xs font-semibold text-foreground">{item.description}</div>
          <div className="text-[11px] text-muted-foreground">
            From {item.sessionType} session on {formatDate(item.sessionDate)}
          </div>
        </div>
        <Badge
          variant={item.status === 'COMPLETED' ? 'success' : overdue ? 'destructive' : 'secondary'}
          className="shrink-0"
        >
          {item.status === 'COMPLETED' ? 'Completed' : overdue ? 'Overdue' : 'Due'}{' '}
          {formatDate(item.due_date)}
        </Badge>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Open ({open.length})</CardTitle>
          <CardDescription>Commitments not yet marked complete</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {open.length === 0 ? (
            <p className="py-2 text-center text-xs text-muted-foreground">Nothing outstanding.</p>
          ) : (
            open.map((item, i) => <Row key={item.id ?? i} item={item} />)
          )}
        </CardContent>
      </Card>

      {done.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Completed ({done.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {done.map((item, i) => (
              <Row key={item.id ?? i} item={item} />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/** Staff-only. Explains WHY a student carries their risk level by laying out
 *  the three signals the system actually flags on, rather than restating the
 *  level as if it were self-evident. */
export function RiskAnalysisTab({
  studentId,
  profile,
}: {
  studentId: string;
  profile: { risk_level: string };
}) {
  const { data: attendance } = useQuery({
    queryKey: ['attendance', studentId, 'summary'],
    queryFn: () => attendanceService.getStudentAttendanceSummary(studentId),
  });
  const { data: academics } = useQuery({
    queryKey: ['academics', studentId, 'record'],
    queryFn: () => academicsService.getStudentRecord(studentId),
  });
  const { data: sessions } = useQuery({
    queryKey: ['counselling', 'sessions', studentId],
    queryFn: () => counsellingService.getSessions(studentId),
  });

  // null means the API has no classes on record — distinct from a low
  // percentage, and it must never render as one.
  const attendancePct = attendance?.overall_percentage ?? undefined;
  const backlogs = academics?.total_active_backlogs;
  const lastSession = sessions?.[0]?.session_date;

  const signals = [
    {
      label: 'Attendance',
      value: attendancePct === undefined ? 'No data' : `${attendancePct}%`,
      triggered: attendancePct !== undefined && attendancePct < 75,
      detail:
        attendancePct === undefined
          ? 'No attendance recorded yet'
          : attendancePct < 75
            ? 'Below the 75% institutional threshold'
            : 'Meeting the 75% threshold',
    },
    {
      label: 'Active backlogs',
      value: backlogs === undefined ? 'No data' : String(backlogs),
      triggered: !!backlogs && backlogs > 0,
      detail: backlogs ? `${backlogs} subject(s) pending clearance` : 'No pending backlogs',
    },
    {
      label: 'Counselling contact',
      value: lastSession ? formatDate(lastSession) : 'Never',
      triggered: !lastSession,
      detail: lastSession ? 'Last recorded session' : 'This student has never been counselled',
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between space-y-0">
          <div>
            <CardTitle className="text-base">Current risk level</CardTitle>
            <CardDescription>
              Set manually by a counsellor — a judgement, not a computed score
            </CardDescription>
          </div>
          <RiskBadge level={profile.risk_level} />
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Risk signals</CardTitle>
          <CardDescription>The three factors this system flags on</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {signals.map((s) => (
            <div
              key={s.label}
              className={cn(
                'flex items-start justify-between gap-3 rounded-xl border p-3',
                s.triggered ? 'border-amber-500/30 bg-amber-500/5' : 'border-border/60 bg-muted/20'
              )}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  {s.triggered ? (
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                  )}
                  <span className="text-xs font-bold text-foreground">{s.label}</span>
                </div>
                <div className="mt-0.5 pl-5 text-[11px] text-muted-foreground">{s.detail}</div>
              </div>
              <span className="shrink-0 text-sm font-black tabular-nums text-foreground">{s.value}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
