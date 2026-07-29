import * as React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { studentService, Student360Data } from '../services/student.service';
import { counsellingService } from '@/features/counselling/services/counselling.service';
import { attendanceService } from '@/features/attendance/services/attendance.service';
import { academicsService } from '@/features/academics/services/academics.service';
import { parentService } from '@/features/parents/services/parent.service';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/components/ui/Table';
import { RiskBadge, StudentAvatar, formatDate } from './StudentPresentation';
import {
  ProfileTab,
  SkillsGoalsTab,
  ActionItemsTab,
  RiskAnalysisTab,
} from './StudentProfileTabs';
import {
  InternshipsTab,
  InterviewsTab,
  AchievementsTab,
  DocumentsTab as ProfileDocumentsTab,
} from './ProfileCollections';
import { cn } from '@/shared/utils/cn';
import {
  User,
  AlertTriangle,
  Plus,
  GraduationCap,
  CalendarCheck,
  MessageSquare,
  PhoneCall,
  Lock,
  FileText,
  CheckCircle2,
  Clock,
  Contact,
  ListChecks,
  Target,
  Briefcase,
  Mic,
  Trophy,
} from 'lucide-react';

interface StudentWorkspaceViewProps {
  workspaceData: Student360Data;
  /** "staff" is the counsellor/faculty/admin case-management view (risk
   * escalation, new-session shortcut, confidential notes). "self" is the
   * student's own view — no case-management controls, no confidential
   * anything. */
  mode: 'staff' | 'self';
}

type TabKey =
  | 'overview'
  | 'profile'
  | 'academics'
  | 'attendance'
  | 'counselling'
  | 'actions'
  | 'risk'
  | 'skills'
  | 'internships'
  | 'interviews'
  | 'achievements'
  | 'parents'
  | 'documents';

const TABS: { key: TabKey; label: string; icon: React.ElementType; staffOnly?: boolean }[] = [
  { key: 'overview', label: 'Overview', icon: User },
  { key: 'profile', label: 'Personal Info', icon: Contact },
  { key: 'academics', label: 'Academics', icon: GraduationCap },
  { key: 'attendance', label: 'Attendance', icon: CalendarCheck },
  { key: 'counselling', label: 'Counselling', icon: MessageSquare },
  { key: 'actions', label: 'Action Items', icon: ListChecks },
  { key: 'risk', label: 'Risk Analysis', icon: AlertTriangle, staffOnly: true },
  { key: 'skills', label: 'Skills & Goals', icon: Target },
  { key: 'internships', label: 'Internships', icon: Briefcase },
  { key: 'interviews', label: 'Interviews', icon: Mic },
  { key: 'achievements', label: 'Achievements', icon: Trophy },
  { key: 'parents', label: 'Parent Communication', icon: PhoneCall, staffOnly: true },
  { key: 'documents', label: 'Documents', icon: FileText },
];

export function StudentWorkspaceView({ workspaceData, mode }: StudentWorkspaceViewProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { hasPermission } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [isRiskModalOpen, setIsRiskModalOpen] = React.useState(false);
  const [newRiskLevel, setNewRiskLevel] = React.useState<string>('MEDIUM');
  const [riskReason, setRiskReason] = React.useState('');

  const { profile, stats, attention_items } = workspaceData;
  const isStaff = mode === 'staff';

  const visibleTabs = TABS.filter((t) => isStaff || !t.staffOnly);
  const requestedTab = searchParams.get('tab') as TabKey | null;
  const activeTab: TabKey =
    requestedTab && visibleTabs.some((t) => t.key === requestedTab) ? requestedTab : 'overview';

  const setTab = (tab: TabKey) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('tab', tab);
      return next;
    });
  };

  const flagRiskMutation = useMutation({
    mutationFn: (vars: { studentId: string; risk_level: string; reason: string }) =>
      studentService.updateRiskFlag(vars.studentId, vars.risk_level, vars.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setIsRiskModalOpen(false);
      setRiskReason('');
    },
  });

  return (
    <>
      {/* Hero header */}
      <div className="relative mb-6 overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-r from-card via-muted/40 to-card p-6 shadow-md md:p-8">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <StudentAvatar name={profile.full_name} size="lg" />
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-black tracking-tight text-foreground">{profile.full_name}</h1>
                {isStaff && <RiskBadge level={profile.risk_level} />}
                {profile.department_name && <Badge variant="outline">{profile.department_name}</Badge>}
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-xs text-muted-foreground">
                <span>
                  Roll: <strong className="text-foreground">{profile.roll_number}</strong>
                </span>
                <span>
                  Reg: <strong className="text-foreground">{profile.registration_number}</strong>
                </span>
                <span>
                  Email: <strong className="text-foreground">{profile.email}</strong>
                </span>
              </div>
            </div>
          </div>

          {isStaff && (
            <div className="flex shrink-0 flex-wrap items-center gap-3">
              {hasPermission('student.risk.update') && (
                <Button size="sm" variant="outline" onClick={() => setIsRiskModalOpen(true)}>
                  <AlertTriangle className="mr-1.5 h-3.5 w-3.5 text-amber-500" />
                  Flag Risk Level
                </Button>
              )}
              {hasPermission('counselling.create') && (
                <Button size="sm" onClick={() => navigate(`/counselling/new?studentId=${profile.id}`)}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  New Session
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 overflow-x-auto border-b border-border/80">
        {visibleTabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setTab(tab.key)}
            className={cn(
              'flex shrink-0 cursor-pointer items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-colors',
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <tab.icon className="h-3.5 w-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <OverviewTab mode={mode} stats={stats} attentionItems={attention_items} profile={profile} />
      )}
      {activeTab === 'profile' && <ProfileTab studentId={profile.id} mode={mode} />}
      {activeTab === 'academics' && <AcademicsTab studentId={profile.id} />}
      {activeTab === 'attendance' && <AttendanceTab studentId={profile.id} />}
      {activeTab === 'counselling' && <CounsellingTab studentId={profile.id} mode={mode} />}
      {activeTab === 'actions' && <ActionItemsTab studentId={profile.id} mode={mode} />}
      {activeTab === 'risk' && isStaff && <RiskAnalysisTab studentId={profile.id} profile={profile} />}
      {activeTab === 'skills' && <SkillsGoalsTab studentId={profile.id} mode={mode} />}
      {/* readOnly drives these collections off the staff endpoints
          (/students/:id/...) instead of the student's own /me routes. */}
      {activeTab === 'internships' && (
        <InternshipsTab studentId={isStaff ? profile.id : undefined} readOnly={isStaff} />
      )}
      {activeTab === 'interviews' && (
        <InterviewsTab
          studentId={isStaff ? profile.id : undefined}
          readOnly={isStaff}
          canObserve={isStaff && hasPermission('counselling.create')}
        />
      )}
      {activeTab === 'achievements' && (
        <AchievementsTab studentId={isStaff ? profile.id : undefined} readOnly={isStaff} />
      )}
      {activeTab === 'parents' && isStaff && <ParentsTab studentId={profile.id} />}
      {activeTab === 'documents' && (
        <ProfileDocumentsTab studentId={isStaff ? profile.id : undefined} readOnly={isStaff} />
      )}

      {/* Risk modal — staff only; the trigger doesn't render in self mode */}
      {isStaff && isRiskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <Card className="w-full max-w-md border-border bg-card shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Flag Student Risk Level
              </CardTitle>
              <CardDescription>Escalate or downgrade risk priority tier</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Select Risk Level</label>
                <select
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-xs font-semibold"
                  value={newRiskLevel}
                  onChange={(e) => setNewRiskLevel(e.target.value)}
                >
                  <option value="LOW">LOW RISK — Normal monitoring</option>
                  <option value="MEDIUM">MEDIUM RISK — Multiple defaulters</option>
                  <option value="HIGH">HIGH RISK — Academic probation</option>
                  <option value="CRITICAL">CRITICAL RISK — Immediate intervention</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Escalation Reason &amp; Notes</label>
                <textarea
                  className="w-full rounded-xl border border-input bg-background p-3 text-xs focus:ring-2 focus:ring-ring"
                  rows={3}
                  placeholder="State reason for risk level change…"
                  value={riskReason}
                  onChange={(e) => setRiskReason(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 border-t border-border/80 pt-2">
                <Button variant="outline" size="sm" onClick={() => setIsRiskModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  isLoading={flagRiskMutation.isPending}
                  disabled={!riskReason.trim()}
                  onClick={() =>
                    flagRiskMutation.mutate({
                      studentId: profile.id,
                      risk_level: newRiskLevel,
                      reason: riskReason,
                    })
                  }
                >
                  Confirm Risk Update
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}

function OverviewTab({
  mode,
  stats,
  attentionItems,
  profile,
}: {
  mode: 'staff' | 'self';
  stats: Student360Data['stats'];
  attentionItems: string[];
  profile: Student360Data['profile'];
}) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {mode === 'self' ? 'Things That Need Your Attention' : 'Attention Items & Alerts'}
            </CardTitle>
            <CardDescription>
              {mode === 'self'
                ? 'Attendance, academic, and risk flags on your record'
                : 'System flagged compliance and academic observations'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {attentionItems.length === 0 ? (
              <EmptyState
                icon={CheckCircle2}
                title={mode === 'self' ? "You're all caught up" : 'No Active Alerts'}
                description={
                  mode === 'self'
                    ? 'Nothing needs your attention right now.'
                    : 'In good standing with zero attention items.'
                }
              />
            ) : (
              attentionItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 rounded-xl border border-border/80 bg-muted/20 p-3.5 text-xs font-medium text-foreground"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-[10px] font-bold text-amber-600">
                    {idx + 1}
                  </span>
                  <span>{item}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Family &amp; Contact</CardTitle>
            <CardDescription>Guardian details on file</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <DetailRow label="Father" value={profile.father_name} sub={profile.father_phone} />
            <DetailRow label="Mother" value={profile.mother_name} sub={profile.mother_phone} />
            <DetailRow label="Guardian" value={profile.guardian_name} sub={profile.guardian_phone} />
            <DetailRow label="Phone" value={profile.phone} />
            <DetailRow label="Batch" value={String(profile.batch_year)} />
            <DetailRow label="Mentor" value={profile.counsellor_name} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{mode === 'self' ? 'My Key Metrics' : 'Key Overview Metrics'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {stats.map((st, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/40 p-3"
            >
              <span className="text-xs font-bold text-muted-foreground">{st.title}</span>
              <span className="text-sm font-black text-foreground">{st.value}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({ label, value, sub }: { label: string; value?: string | null; sub?: string | null }) {
  return (
    <div className="rounded-xl border border-border/60 bg-muted/20 p-3">
      <div className="text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="mt-1 text-xs font-bold text-foreground">{value || 'Not provided'}</div>
      {sub && <div className="font-mono text-[11px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

/** Exported so the student's own My Profile page renders the identical
 *  read-only academic view — one implementation, so the two portals can never
 *  disagree about a student's marks. */
export function AcademicsTab({ studentId }: { studentId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['academics', studentId, 'record'],
    queryFn: () => academicsService.getStudentRecord(studentId),
  });

  if (isLoading) return <TabSkeleton />;
  if (isError) return <TabError message="Could not load the academic record." />;
  if (!data || data.semesters.length === 0) {
    return (
      <EmptyState
        icon={GraduationCap}
        title="No marks recorded yet"
        description="Semester results appear here once faculty enter marks or an administrator imports them. Students never enter their own marks."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricTile label="CGPA" value={data.cgpa?.toFixed(2) ?? 'No data'} />
        <MetricTile label="Latest SGPA" value={data.latest_sgpa?.toFixed(2) ?? 'No data'} />
        <MetricTile label="Active backlogs" value={String(data.total_active_backlogs)} />
        <MetricTile label="Semesters on record" value={String(data.semesters.length)} />
      </div>

      {data.semesters.map((sem) => (
        <Card key={sem.semester_id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base">Semester {sem.semester_name}</CardTitle>
              <CardDescription>
                {sem.sgpa != null ? `SGPA ${sem.sgpa.toFixed(2)}` : 'SGPA not calculated'}
                {sem.cgpa != null ? ` • CGPA ${sem.cgpa.toFixed(2)}` : ''}
                {sem.total_credits != null ? ` • ${sem.total_credits} credits` : ''}
              </CardDescription>
            </div>
            {sem.active_backlogs > 0 && <Badge variant="warning">{sem.active_backlogs} backlog(s)</Badge>}
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Mid 1</TableHead>
                  <TableHead>Mid 2</TableHead>
                  <TableHead>Internal</TableHead>
                  <TableHead>External</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Result</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sem.subjects.map((s) => (
                  <TableRow key={s.subject_id}>
                    <TableCell>
                      <div className="font-bold text-foreground">{s.subject_code}</div>
                      <div className="text-[11px] text-muted-foreground">{s.subject_name}</div>
                    </TableCell>
                    <MarkCell value={s.mid_1} />
                    <MarkCell value={s.mid_2} />
                    <MarkCell value={s.internal} />
                    <MarkCell value={s.external} />
                    <TableCell className="tabular-nums">
                      {s.total_obtained != null && s.total_max != null
                        ? `${s.total_obtained} / ${s.total_max}`
                        : '—'}
                    </TableCell>
                    <TableCell className="font-bold">{s.grade ?? '—'}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          s.result === 'PASS' ? 'success' : s.result === 'FAIL' ? 'destructive' : 'secondary'
                        }
                      >
                        {s.result === 'IN_PROGRESS' ? 'In progress' : s.result}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function MarkCell({ value }: { value?: number | null }) {
  return <TableCell className="tabular-nums">{value ?? <span className="text-muted-foreground/60">—</span>}</TableCell>;
}

export function AttendanceTab({ studentId }: { studentId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['attendance', studentId, 'summary'],
    queryFn: () => attendanceService.getStudentAttendanceSummary(studentId),
  });

  if (isLoading) return <TabSkeleton />;
  if (isError) return <TabError message="Could not load attendance." />;
  // A null overall percentage means nothing has been recorded — the same
  // empty state as having no subject rows, never a figure.
  if (!data || data.overall_percentage === null || data.subject_summaries.length === 0) {
    return (
      <EmptyState
        icon={CalendarCheck}
        title="No attendance recorded yet"
        description="Subject-wise attendance appears here once faculty record it or an administrator imports it."
      />
    );
  }

  const overall = data.overall_percentage;
  const low = overall < 75;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Overall attendance</CardTitle>
          <CardDescription>
            {low ? 'Below the 75% institutional threshold' : 'Meeting the 75% institutional threshold'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <span
              className={cn(
                'text-4xl font-black tabular-nums',
                low ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'
              )}
            >
              {overall}%
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted/70">
              <div
                className={cn('h-full rounded-full', low ? 'bg-rose-500' : 'bg-emerald-500')}
                style={{ width: `${Math.min(100, Math.max(0, overall))}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Subject-wise breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Attended</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Percentage</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.subject_summaries.map((s) => {
                const subjectLow = s.percentage < 75;
                return (
                  <TableRow key={s.subject_id}>
                    <TableCell>
                      <div className="font-bold text-foreground">{s.subject_code}</div>
                      <div className="text-[11px] text-muted-foreground">{s.subject_name}</div>
                    </TableCell>
                    <TableCell className="tabular-nums">{s.attended_classes}</TableCell>
                    <TableCell className="tabular-nums">{s.total_classes}</TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          'font-bold tabular-nums',
                          subjectLow ? 'text-rose-600 dark:text-rose-400' : 'text-foreground'
                        )}
                      >
                        {s.percentage}%
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export function CounsellingTab({ studentId, mode }: { studentId: string; mode: 'staff' | 'self' }) {
  // A student reads their own history through /my-sessions, which resolves the
  // student from the token; staff read the roster endpoint by id.
  const { data, isLoading, isError } = useQuery({
    queryKey: ['counselling', 'sessions', studentId, mode],
    queryFn: () =>
      mode === 'self' ? counsellingService.getMySessions() : counsellingService.getSessions(studentId),
  });

  if (isLoading) return <TabSkeleton />;
  if (isError) return <TabError message="Could not load counselling history." />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No counselling sessions yet"
        description={
          mode === 'self'
            ? 'Sessions your counsellor records with you will appear here.'
            : 'Record the first session to start building this student’s history.'
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {data.map((session) => (
        <Card key={session.id}>
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                {session.session_type}
                <Badge variant="outline">{session.mode.replace('_', ' ')}</Badge>
                {session.confidential && (
                  <Badge variant="warning">
                    <Lock className="h-3 w-3" /> Confidential
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>{formatDate(session.session_date)}</CardDescription>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {session.risk_assessment && session.risk_assessment !== 'NONE' && (
                <RiskBadge level={session.risk_assessment} />
              )}
              {session.student_acknowledged ? (
                <Badge variant="success">
                  <CheckCircle2 className="h-3 w-3" /> Acknowledged
                </Badge>
              ) : (
                <Badge variant="secondary">
                  <Clock className="h-3 w-3" /> Awaiting acknowledgement
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Section title="Observations">{session.observations}</Section>
            {session.recommendations && <Section title="Recommendations">{session.recommendations}</Section>}
            {session.student_commitments && (
              <Section title="Student commitments">{session.student_commitments}</Section>
            )}

            {/* Rendered only when the API actually returned notes. For a
                student viewer this field is always null server-side, so this
                block cannot appear in the self view. */}
            {session.confidential_notes && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5">
                <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest text-amber-700 dark:text-amber-400">
                  <Lock className="h-3 w-3" /> Confidential — staff only
                </div>
                <p className="text-xs leading-relaxed text-foreground">{session.confidential_notes}</p>
              </div>
            )}

            {session.action_items.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">
                  Action items
                </div>
                {session.action_items.map((item, i) => (
                  <div
                    key={item.id ?? i}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border/70 bg-muted/20 p-3"
                  >
                    <span className="text-xs font-medium text-foreground">{item.description}</span>
                    <Badge variant={item.status === 'COMPLETED' ? 'success' : 'secondary'}>
                      {item.status ?? 'PENDING'} • {formatDate(item.due_date)}
                    </Badge>
                  </div>
                ))}
              </div>
            )}

            {session.follow_up_required && session.follow_up_date && (
              <div className="text-xs font-semibold text-muted-foreground">
                Follow-up scheduled for {formatDate(session.follow_up_date)}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">{title}</div>
      <p className="text-xs leading-relaxed text-foreground">{children}</p>
    </div>
  );
}

function ParentsTab({ studentId }: { studentId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['parent-communication', studentId],
    queryFn: () => parentService.getStudentCommunications(studentId),
  });

  if (isLoading) return <TabSkeleton />;
  if (isError) return <TabError message="Could not load parent communication history." />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={PhoneCall}
        title="No parent communication logged"
        description="Calls, meetings and emails with this student’s parents will appear here once logged."
      />
    );
  }

  return (
    <div className="space-y-4">
      {data.map((c) => (
        <Card key={c.id}>
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="text-base">
                {c.parent_name} <span className="font-normal text-muted-foreground">({c.relation})</span>
              </CardTitle>
              <CardDescription>
                {formatDate(c.communication_date)} • {c.mode.replace('_', ' ')} • {c.contact_number}
              </CardDescription>
            </div>
            <Badge
              variant={
                c.outcome === 'POSITIVE'
                  ? 'success'
                  : c.outcome === 'CONCERNING'
                    ? 'destructive'
                    : c.outcome === 'UNRESPONSIVE'
                      ? 'warning'
                      : 'secondary'
              }
            >
              {c.outcome}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            <Section title="Summary">{c.summary}</Section>
            {c.concerns && <Section title="Concerns raised">{c.concerns}</Section>}
            {c.action_items && <Section title="Agreed actions">{c.action_items}</Section>}
            {c.follow_up_date && (
              <div className="text-xs font-semibold text-muted-foreground">
                Follow-up on {formatDate(c.follow_up_date)}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Personal information                                                       */
/* -------------------------------------------------------------------------- */
function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">{label}</div>
        <div className="mt-1.5 text-2xl font-black tracking-tight text-foreground">{value}</div>
      </CardContent>
    </Card>
  );
}

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
