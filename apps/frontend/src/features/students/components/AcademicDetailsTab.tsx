/**
 * Section 2 of the Student 360° Workspace — Academic Details.
 *
 * Read-only throughout: everything here is ERP/admin owned, and there is no
 * write path from this component to any of it.
 *
 * Every figure comes from the API — the academics record, the attendance
 * summary and the ERP block on the profile. Where a value has not been
 * recorded, the card says so. Nothing on this page renders a placeholder
 * figure: a student reads these numbers as their own academic standing, and
 * an invented CGPA or attendance percentage is worse than a blank.
 */
import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Award,
  BadgeCheck,
  BookOpenCheck,
  Briefcase,
  CalendarCheck,
  ClipboardList,
  GraduationCap,
  Fingerprint,
  Landmark,
  ListChecks,
  TrendingUp,
} from 'lucide-react';
import { academicsService } from '@/features/academics/services/academics.service';
import { attendanceService } from '@/features/attendance/services/attendance.service';
import { Student360Data } from '../services/student.service';
import {
  ADMISSION_TYPE_LABELS,
  StudentSelfProfile,
  profileService,
} from '../services/profile.service';
import { CollapsibleCard, ReadOnlyBadge } from './ProfileWorkspaceKit';
import { cn } from '@/shared/utils/cn';

interface AcademicDetailsTabProps {
  /** Institution-owned identity/stat header, shared with the counsellor view. */
  workspaceData: Student360Data;
  /** The ERP block plus identity. Optional so the counsellor workspace can
   *  render this tab from workspace data alone. */
  profile?: StudentSelfProfile;
  isStudentMode?: boolean;
}

const NOT_RECORDED = 'Not recorded';

function Value({ label, value, tone }: { label: string; value?: React.ReactNode; tone?: 'good' | 'warn' | 'bad' }) {
  const empty = value === null || value === undefined || value === '' || value === NOT_RECORDED;
  return (
    <div className="rounded-2xl border border-border/40 bg-muted/30 p-3">
      <span className="mb-0.5 block text-[10px] font-black uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <span
        className={cn(
          'text-xs font-extrabold',
          empty && 'italic font-bold text-muted-foreground/50',
          !empty && tone === 'good' && 'text-emerald-600',
          !empty && tone === 'warn' && 'text-amber-600',
          !empty && tone === 'bad' && 'text-rose-600',
          !empty && !tone && 'text-foreground'
        )}
      >
        {empty ? NOT_RECORDED : value}
      </span>
    </div>
  );
}

function Grid({ children, cols = 3 }: { children: React.ReactNode; cols?: 2 | 3 | 4 }) {
  return (
    <div
      className={cn(
        'grid grid-cols-2 gap-3',
        cols === 2 && 'sm:grid-cols-2',
        cols === 3 && 'sm:grid-cols-3',
        cols === 4 && 'sm:grid-cols-2 lg:grid-cols-4'
      )}
    >
      {children}
    </div>
  );
}

/** Horizontally scrollable table shell — wide result tables must scroll in
 *  their own container rather than pushing the page sideways on a phone. */
function ScrollTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[520px] border-collapse text-left text-[11px]">{children}</table>
    </div>
  );
}

function Th({ children, align = 'left' }: { children: React.ReactNode; align?: 'left' | 'right' }) {
  return (
    <th
      className={cn(
        'border-b border-border/60 px-2 py-2 text-[10px] font-black uppercase tracking-wider text-muted-foreground',
        align === 'right' && 'text-right'
      )}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  align = 'left',
  className,
}: {
  children: React.ReactNode;
  align?: 'left' | 'right';
  className?: string;
}) {
  return (
    <td
      className={cn(
        'border-b border-border/30 px-2 py-2 font-semibold text-foreground',
        align === 'right' && 'text-right tabular-nums',
        className
      )}
    >
      {children}
    </td>
  );
}

const dash = <span className="text-muted-foreground/40">—</span>;
const num = (v?: number | string | null, suffix = '') =>
  v === null || v === undefined || v === '' ? undefined : `${v}${suffix}`;

export function AcademicDetailsTab({ workspaceData, profile }: AcademicDetailsTabProps) {
  const studentId = workspaceData.profile.id;
  const identity = profile?.identity;
  const academic = profile?.academic;

  const { data: record } = useQuery({
    queryKey: ['academics', studentId, 'record'],
    queryFn: () => academicsService.getStudentRecord(studentId),
  });

  const { data: attendance } = useQuery({
    queryKey: ['attendance', studentId, 'summary'],
    queryFn: () => attendanceService.getStudentAttendanceSummary(studentId),
  });

  const { data: backlogs } = useQuery({
    queryKey: ['academics', studentId, 'backlogs'],
    queryFn: () => academicsService.getStudentBacklogs(studentId),
  });

  const semesters = record?.semesters ?? [];
  const creditsEarned = semesters.reduce((sum, s) => sum + (s.total_credits ?? 0), 0);
  const creditsRequired = academic?.total_credits_required ?? null;
  const creditsRemaining =
    creditsRequired !== null ? Math.max(0, creditsRequired - creditsEarned) : null;

  const attendancePct = attendance?.overall_percentage ?? null;
  const activeBacklogs = (backlogs ?? []).filter((b) => b.status === 'ACTIVE');
  const clearedBacklogs = (backlogs ?? []).filter((b) => b.status === 'CLEARED');

  // The current semester is the highest-numbered block the ERP has published.
  const currentSemester = semesters[semesters.length - 1];
  const currentSemesterAttendance = attendance?.monthly_trend?.length
    ? attendance.monthly_trend[attendance.monthly_trend.length - 1]
    : undefined;

  return (
    <div className="space-y-3">
      <p className="flex items-center gap-2 rounded-2xl border border-border/60 bg-muted/20 px-4 py-2.5 text-[11px] font-medium text-muted-foreground">
        <Fingerprint className="h-3.5 w-3.5 shrink-0 text-brand-600" />
        Maintained by the college from ERP records. If something here is wrong, raise it with your counsellor or the
        administration office — it cannot be edited from this page.
      </p>

      {/* A. Student identity */}
      <CollapsibleCard
        id="identity"
        title="A. Student Identity"
        description="Your registration numbers"
        icon={Fingerprint}
        accent="brand"
        defaultOpen
        badge={<ReadOnlyBadge />}
      >
        <Grid cols={4}>
          <Value label="Roll number" value={workspaceData.profile.roll_number} />
          <Value label="Registration number" value={workspaceData.profile.registration_number} />
          <Value label="Admission number" value={academic?.admission_number} />
          <Value label="ABC ID" value={academic?.abc_id} />
        </Grid>
      </CollapsibleCard>

      {/* B. Admission details */}
      <CollapsibleCard
        id="admission"
        title="B. Admission Details"
        description="How and when you joined"
        icon={Landmark}
        accent="indigo"
        badge={<ReadOnlyBadge />}
      >
        <Grid cols={4}>
          <Value
            label="Admission type"
            value={academic?.admission_type ? ADMISSION_TYPE_LABELS[academic.admission_type] ?? academic.admission_type : undefined}
          />
          <Value label="Academic year" value={academic?.academic_year} />
          <Value label="Joining year" value={num(academic?.joining_year ?? workspaceData.profile.batch_year)} />
          <Value label="Current year" value={identity?.study_year ? `Year ${identity.study_year}` : undefined} />
          <Value label="Current semester" value={identity?.semester_name} />
          <Value label="Admission date" value={academic?.admission_date} />
        </Grid>
      </CollapsibleCard>

      {/* C. Academic information */}
      <CollapsibleCard
        id="academic-info"
        title="C. Academic Information"
        description="Programme, branch and the staff assigned to you"
        icon={GraduationCap}
        accent="purple"
        badge={<ReadOnlyBadge />}
      >
        <Grid cols={3}>
          <Value label="Program" value={identity?.program} />
          <Value label="Branch" value={identity?.branch ?? workspaceData.profile.department_name} />
          <Value label="Department" value={workspaceData.profile.department_name} />
          <Value label="Section" value={identity?.section_name} />
          <Value label="Mentor" value={identity?.mentor_name} />
          <Value label="Counsellor" value={identity?.counsellor_name ?? workspaceData.profile.counsellor_name} />
        </Grid>
      </CollapsibleCard>

      {/* D. Academic performance */}
      <CollapsibleCard
        id="performance"
        title="D. Academic Performance"
        description="CGPA, semester-wise SGPA and credits"
        icon={TrendingUp}
        accent="emerald"
        defaultOpen
        badge={<ReadOnlyBadge />}
      >
        <div className="space-y-4">
          <Grid cols={4}>
            <Value label="Current CGPA" value={num(record?.cgpa?.toFixed(2))} tone="good" />
            <Value label="Latest SGPA" value={num(record?.latest_sgpa?.toFixed(2))} />
            <Value label="Total credits earned" value={semesters.length ? creditsEarned : undefined} />
            <Value
              label="Credits remaining"
              value={creditsRemaining !== null ? creditsRemaining : undefined}
            />
          </Grid>

          {semesters.length === 0 ? (
            <p className="text-[11px] italic text-muted-foreground/60">
              No semester results have been published yet.
            </p>
          ) : (
            <div>
              <p className="mb-2 text-[11px] font-black uppercase tracking-wider text-muted-foreground">
                Semester-wise SGPA
              </p>
              <div className="flex flex-wrap gap-2">
                {semesters.map((s) => (
                  <div
                    key={s.semester_id}
                    className="min-w-[92px] flex-1 rounded-2xl border border-border/50 bg-muted/30 p-2.5 text-center"
                  >
                    <span className="block text-[10px] font-black uppercase text-muted-foreground">
                      Sem {s.semester_number}
                    </span>
                    <span className="text-base font-black tabular-nums text-foreground">
                      {s.sgpa != null ? s.sgpa.toFixed(2) : dash}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CollapsibleCard>

      {/* E. Attendance */}
      <CollapsibleCard
        id="attendance"
        title="E. Attendance"
        description="Overall, current semester and the monthly trend"
        icon={CalendarCheck}
        accent="sky"
        badge={<ReadOnlyBadge />}
      >
        <div className="space-y-4">
          <Grid cols={3}>
            <Value
              label="Overall attendance"
              value={attendancePct !== null ? `${attendancePct}%` : undefined}
              tone={attendancePct === null ? undefined : attendancePct >= 75 ? 'good' : attendancePct >= 65 ? 'warn' : 'bad'}
            />
            <Value
              label="Classes attended"
              value={attendance?.total_classes ? `${attendance.attended_classes} of ${attendance.total_classes}` : undefined}
            />
            <Value
              label="This month"
              value={currentSemesterAttendance ? `${currentSemesterAttendance.percentage}%` : undefined}
            />
          </Grid>

          {attendancePct !== null && (
            <p className="rounded-xl border border-border/50 bg-muted/20 p-3 text-[11px] font-semibold text-muted-foreground">
              {attendancePct >= 75
                ? 'Above the 75% examination eligibility threshold.'
                : attendancePct >= 65
                  ? 'In the 65–74% condonation range — eligibility needs approval.'
                  : 'Below the 65% condonation floor. Speak to your counsellor.'}
            </p>
          )}

          {attendance?.monthly_trend?.length ? (
            <div>
              <p className="mb-2 text-[11px] font-black uppercase tracking-wider text-muted-foreground">
                Monthly trend
              </p>
              <div className="space-y-1.5">
                {attendance.monthly_trend.map((m) => (
                  <div key={m.month} className="flex items-center gap-3">
                    <span className="w-16 shrink-0 text-[10px] font-bold text-muted-foreground">{m.label}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted/70">
                      <div
                        className={cn('h-full rounded-full', m.percentage < 75 ? 'bg-rose-500' : 'bg-emerald-500')}
                        style={{ width: `${Math.min(100, Math.max(0, m.percentage))}%` }}
                      />
                    </div>
                    <span className="w-20 shrink-0 text-right text-[10px] font-bold tabular-nums text-foreground">
                      {m.percentage}%{' '}
                      <span className="text-muted-foreground/70">
                        ({m.attended_classes}/{m.total_classes})
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-[11px] italic text-muted-foreground/60">No attendance has been recorded yet.</p>
          )}
        </div>
      </CollapsibleCard>

      {/* F. Internal marks */}
      <CollapsibleCard
        id="internal-marks"
        title="F. Internal Marks"
        description={
          currentSemester ? `Subject-wise for ${currentSemester.semester_name}` : 'Subject-wise assessment marks'
        }
        icon={ClipboardList}
        accent="amber"
        badge={<ReadOnlyBadge />}
      >
        {!currentSemester || currentSemester.subjects.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">No marks have been published yet.</p>
        ) : (
          <ScrollTable>
            <thead>
              <tr>
                <Th>Subject</Th>
                <Th align="right">Mid 1</Th>
                <Th align="right">Mid 2</Th>
                <Th align="right">Internal</Th>
                <Th align="right">External</Th>
                <Th align="right">Total</Th>
              </tr>
            </thead>
            <tbody>
              {currentSemester.subjects.map((s) => (
                <tr key={s.subject_id}>
                  <Td>
                    <span className="block font-bold text-foreground">{s.subject_name}</span>
                    <span className="font-mono text-[10px] text-muted-foreground">{s.subject_code}</span>
                  </Td>
                  <Td align="right">{s.mid_1 ?? dash}</Td>
                  <Td align="right">{s.mid_2 ?? dash}</Td>
                  <Td align="right">{s.internal ?? dash}</Td>
                  <Td align="right">{s.external ?? dash}</Td>
                  <Td align="right">
                    {s.total_obtained != null && s.total_max != null
                      ? `${s.total_obtained}/${s.total_max}`
                      : dash}
                  </Td>
                </tr>
              ))}
            </tbody>
          </ScrollTable>
        )}
      </CollapsibleCard>

      {/* G. Semester results */}
      <CollapsibleCard
        id="results"
        title="G. Semester Results"
        description="Published results, semester by semester"
        icon={BookOpenCheck}
        accent="emerald"
        badge={<ReadOnlyBadge />}
      >
        {semesters.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">No semester results have been published yet.</p>
        ) : (
          <ScrollTable>
            <thead>
              <tr>
                <Th>Semester</Th>
                <Th align="right">SGPA</Th>
                <Th align="right">Credits</Th>
                <Th align="right">Result</Th>
                <Th align="right">Backlogs</Th>
              </tr>
            </thead>
            <tbody>
              {semesters.map((s) => {
                const failed = s.subjects.filter((sub) => sub.result === 'FAIL').length;
                const inProgress = s.subjects.some((sub) => sub.result === 'IN_PROGRESS');
                return (
                  <tr key={s.semester_id}>
                    <Td>{s.semester_name}</Td>
                    <Td align="right">{s.sgpa != null ? s.sgpa.toFixed(2) : dash}</Td>
                    <Td align="right">{s.total_credits ?? dash}</Td>
                    <Td align="right">
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-[10px] font-extrabold',
                          inProgress
                            ? 'bg-muted text-muted-foreground'
                            : failed > 0
                              ? 'bg-rose-500/10 text-rose-600'
                              : 'bg-emerald-500/10 text-emerald-600'
                        )}
                      >
                        {inProgress ? 'In progress' : failed > 0 ? 'Fail' : 'Pass'}
                      </span>
                    </Td>
                    <Td align="right">{s.active_backlogs}</Td>
                  </tr>
                );
              })}
            </tbody>
          </ScrollTable>
        )}
      </CollapsibleCard>

      {/* H. Backlogs */}
      <CollapsibleCard
        id="backlogs"
        title="H. Backlogs"
        description="Active and cleared subjects"
        icon={ListChecks}
        accent={activeBacklogs.length > 0 ? 'rose' : 'emerald'}
        badge={<ReadOnlyBadge />}
      >
        <div className="space-y-4">
          <Grid cols={3}>
            <Value
              label="Active backlogs"
              value={backlogs ? activeBacklogs.length : undefined}
              tone={activeBacklogs.length > 0 ? 'bad' : 'good'}
            />
            <Value label="Cleared backlogs" value={backlogs ? clearedBacklogs.length : undefined} />
            <Value
              label="Improvement exams"
              value={backlogs ? clearedBacklogs.filter((b) => b.cleared_at_semester_id).length : undefined}
            />
          </Grid>

          {backlogs && backlogs.length > 0 && (
            <ScrollTable>
              <thead>
                <tr>
                  <Th>Subject</Th>
                  <Th align="right">Status</Th>
                  <Th align="right">Cleared on</Th>
                </tr>
              </thead>
              <tbody>
                {backlogs.map((b) => (
                  <tr key={b.id}>
                    <Td>
                      <span className="block font-bold text-foreground">{b.subject_name ?? 'Subject'}</span>
                      <span className="font-mono text-[10px] text-muted-foreground">{b.subject_code}</span>
                    </Td>
                    <Td align="right">
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-[10px] font-extrabold',
                          b.status === 'ACTIVE' ? 'bg-rose-500/10 text-rose-600' : 'bg-emerald-500/10 text-emerald-600'
                        )}
                      >
                        {b.status}
                      </span>
                    </Td>
                    <Td align="right">{b.cleared_date ?? dash}</Td>
                  </tr>
                ))}
              </tbody>
            </ScrollTable>
          )}
          {backlogs && backlogs.length === 0 && (
            <p className="text-[11px] font-semibold text-emerald-600">No backlogs on record — clean slate.</p>
          )}
        </div>
      </CollapsibleCard>

      {/* I. Entrance examination details */}
      <CollapsibleCard
        id="entrance"
        title="I. Entrance Examination Details"
        description="Qualifying marks and ranks from admission"
        icon={BadgeCheck}
        accent="indigo"
        badge={<ReadOnlyBadge />}
      >
        <Grid cols={4}>
          <Value label="SSC percentage" value={num(academic?.ssc_percentage, '%')} />
          <Value label="Intermediate percentage" value={num(academic?.intermediate_percentage, '%')} />
          <Value label="EAMCET rank" value={num(academic?.eamcet_rank)} />
          <Value label="JEE rank" value={num(academic?.jee_rank)} />
        </Grid>
      </CollapsibleCard>

      {/* J. Scholarships */}
      <CollapsibleCard
        id="scholarships"
        title="J. Scholarships"
        description="Fee reimbursement and scholarship status"
        icon={Award}
        accent="amber"
        badge={<ReadOnlyBadge />}
      >
        <Grid cols={3}>
          <Value label="Scholarship name" value={academic?.scholarship_name} />
          <Value label="Scholarship status" value={academic?.scholarship_status} />
          <Value label="Fee reimbursement" value={academic?.fee_reimbursement_status} />
        </Grid>
      </CollapsibleCard>

      {/* K. Placement readiness */}
      <CollapsibleCard
        id="placement"
        title="K. Placement Readiness"
        description="What recruiters and the placement cell can see"
        icon={Briefcase}
        accent="sky"
        badge={<ReadOnlyBadge />}
      >
        <PlacementReadiness
          profile={profile}
          attendancePct={attendancePct}
          cgpa={record?.cgpa ?? null}
          activeBacklogs={activeBacklogs.length}
          hasBacklogData={!!backlogs}
        />
      </CollapsibleCard>
    </div>
  );
}

/**
 * Placement eligibility is *derived and labelled as such*, from the two rules
 * the institution actually applies (attendance ≥ 75%, no active backlogs). It
 * is never presented as an official placement-cell decision, and it stays
 * blank while either input is unknown rather than guessing.
 */
function PlacementReadiness({
  profile,
  attendancePct,
  cgpa,
  activeBacklogs,
  hasBacklogData,
}: {
  profile?: StudentSelfProfile;
  attendancePct: number | null;
  cgpa: number | null;
  activeBacklogs: number;
  hasBacklogData: boolean;
}) {
  const { data: internships } = useQuery({
    queryKey: ['students', 'me', 'internships'],
    queryFn: profileService.listInternships,
    enabled: !!profile,
  });

  const { data: achievements } = useQuery({
    queryKey: ['students', profile?.identity.student_id, 'achievements'],
    queryFn: profileService.listAchievements,
    enabled: !!profile,
  });

  const certificationCount = (achievements ?? []).filter((a) => a.category === 'CERTIFICATION').length;
  const ongoing = (internships ?? []).filter((i) => i.status === 'ONGOING').length;
  const completed = (internships ?? []).filter((i) => i.status === 'COMPLETED').length;

  const codingProfiles = [
    ['LeetCode', profile?.leetcode_url],
    ['CodeChef', profile?.codechef_url],
    ['HackerRank', profile?.hackerrank_url],
    ['Codeforces', profile?.codeforces_url],
    ['GitHub', profile?.github_url],
  ].filter(([, url]) => !!url) as [string, string][];

  const canDecide = attendancePct !== null && hasBacklogData;
  const eligible = canDecide && attendancePct >= 75 && activeBacklogs === 0;

  return (
    <div className="space-y-4">
      <Grid cols={4}>
        <Value
          label="Resume uploaded"
          value={profile ? (profile.resume_url ? 'Yes' : 'Not uploaded') : undefined}
          tone={profile?.resume_url ? 'good' : 'warn'}
        />
        <Value
          label="Internship status"
          value={
            internships
              ? ongoing > 0
                ? `${ongoing} ongoing`
                : completed > 0
                  ? `${completed} completed`
                  : 'None recorded'
              : undefined
          }
        />
        <Value
          label="Placement eligibility"
          value={canDecide ? (eligible ? 'Meets criteria' : 'Criteria not met') : undefined}
          tone={canDecide ? (eligible ? 'good' : 'warn') : undefined}
        />
        <Value label="Certifications" value={achievements ? certificationCount : undefined} />
      </Grid>

      <div className="rounded-2xl border border-border/50 bg-muted/20 p-3">
        <p className="mb-2 text-[10px] font-black uppercase tracking-wider text-muted-foreground">
          Coding profiles
        </p>
        {codingProfiles.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">
            No coding profiles added yet — add them under Professional Links.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {codingProfiles.map(([name, url]) => (
              <a
                key={name}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-border/60 bg-card px-2.5 py-1 text-[11px] font-bold text-brand-600 hover:underline"
              >
                {name}
              </a>
            ))}
          </div>
        )}
      </div>

      <p className="text-[10px] text-muted-foreground/80">
        Eligibility shown here is derived from attendance (≥75%) and active backlogs
        {cgpa !== null ? `, alongside a CGPA of ${cgpa.toFixed(2)}` : ''}. The placement cell's decision is final.
      </p>
    </div>
  );
}
