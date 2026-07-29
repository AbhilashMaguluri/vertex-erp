import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { studentService, Student360Data } from '../services/student.service';
import { profileService, StudentSelfProfile } from '../services/profile.service';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { AcademicsTab, AttendanceTab } from '../components/StudentWorkspaceView';
import { RequestCorrectionModal } from '../components/RequestCorrectionModal';
import {
  GraduationCap,
  Award,
  CalendarCheck,
  Building2,
  AlertTriangle,
  FileText,
} from 'lucide-react';

export function Student360AcademicPage() {
  const [modalOpen, setModalOpen] = React.useState(false);
  const [targetSection, setTargetSection] = React.useState('Academic Record');
  const [targetCurrVal, setTargetCurrVal] = React.useState('');

  const openCorrectionModal = (section: string, currVal?: string) => {
    setTargetSection(section);
    setTargetCurrVal(currVal || '');
    setModalOpen(true);
  };

  const {
    data: workspaceData,
    isLoading: isLoadingWorkspace,
    error: workspaceError,
  } = useQuery<Student360Data>({
    queryKey: ['students', 'me', 'workspace'],
    queryFn: studentService.getMyWorkspace,
  });

  const {
    data: profile,
    isLoading: isLoadingProfile,
  } = useQuery<StudentSelfProfile>({
    queryKey: ['students', 'me', 'profile'],
    queryFn: profileService.getSelfProfile,
  });

  if (isLoadingWorkspace || isLoadingProfile) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-44 rounded-3xl" />
        <Skeleton className="h-64 rounded-3xl" />
        <Skeleton className="h-64 rounded-3xl" />
      </div>
    );
  }

  if (workspaceError || !workspaceData) {
    return (
      <EmptyState
        icon={GraduationCap}
        title="Unable to load Academic 360 Record"
        description="Could not retrieve academic records from the central database."
      />
    );
  }

  const { profile: studentProf } = workspaceData;
  const academic = profile?.academic;

  const attendanceStat = workspaceData.stats?.find((s) => s.title.toLowerCase().includes('attendance'));
  const sgpaStat = workspaceData.stats?.find((s) => s.title.toLowerCase().includes('sgpa'));

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Student 360 Portal', to: '/student-360/personal' }, { label: 'Academic Details' }]} />

      {/* ACADEMIC HERO SUMMARY BANNER */}
      <div className="rounded-3xl border border-border/80 bg-gradient-to-r from-card via-muted/30 to-card p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-brand-500/30 bg-brand-500/10 text-brand-600 font-bold">
                Institution-Managed Academic Record
              </Badge>
              <span className="text-xs font-mono text-muted-foreground">Single Source of Truth</span>
            </div>
            <h1 className="text-2xl font-black text-foreground">{studentProf.full_name}'s Academic Snapshot</h1>
            <p className="text-xs text-muted-foreground">
              Department of {studentProf.department_name || 'Engineering'} • Roll: <strong className="text-foreground">{studentProf.roll_number}</strong>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Button
              size="sm"
              variant="outline"
              className="border-amber-500/40 text-amber-700 hover:bg-amber-500/10 font-bold"
              onClick={() => openCorrectionModal('Academic Summary', `CGPA: ${sgpaStat?.description || ''}`)}
            >
              <AlertTriangle className="mr-1.5 h-3.5 w-3.5 text-amber-500" />
              Report Incorrect Academic Info
            </Button>
          </div>
        </div>
      </div>

      {/* A. ENROLLMENT & PROGRAMME CARD */}
      <Card className="rounded-3xl border-border/80 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Building2 className="h-4 w-4 text-brand-500" /> Enrollment &amp; Department Details
              </CardTitle>
              <Badge variant="secondary" className="text-[10px] font-bold bg-slate-500/10 text-slate-700 border-slate-300">
                Managed by Academic Office
              </Badge>
            </div>
            <CardDescription className="text-xs">Current branch, section, semester, and mentors</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs font-bold text-amber-700 border-amber-500/30 hover:bg-amber-500/10"
            onClick={() => openCorrectionModal('Enrollment & Department Details', `${studentProf.department_name} - ${studentProf.roll_number}`)}
          >
            Request Correction
          </Button>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          <AcademicTile label="Department" value={studentProf.department_name || 'N/A'} />
          <AcademicTile label="Admission Number" value={academic?.admission_number || studentProf.registration_number} />
          <AcademicTile label="Admission Type" value={academic?.admission_type || 'Convenor'} />
          <AcademicTile label="Batch Year" value={String(studentProf.batch_year)} />
          <AcademicTile label="Counsellor" value={studentProf.counsellor_name || 'Assigned Counsellor'} />
          <AcademicTile label="Status" value={studentProf.status} />
          <AcademicTile label="ABC ID" value={academic?.abc_id || 'Not generated'} />
          <AcademicTile label="Fee Reimbursement" value={academic?.fee_reimbursement_status || 'Eligible'} />
        </CardContent>
      </Card>

      {/* B. ATTENDANCE SECTION */}
      <Card className="rounded-3xl border-border/80 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <CalendarCheck className="h-4 w-4 text-emerald-500" /> Attendance Overview &amp; Subject Breakdown
              </CardTitle>
              <Badge variant="secondary" className="text-[10px] font-bold bg-emerald-500/10 text-emerald-700 border-emerald-300">
                Managed by Faculty
              </Badge>
            </div>
            <CardDescription className="text-xs">Overall percentage and subject-wise class attendance</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs font-bold text-amber-700 border-amber-500/30 hover:bg-amber-500/10"
            onClick={() => openCorrectionModal('Attendance Record', attendanceStat?.value || '')}
          >
            Request Correction
          </Button>
        </CardHeader>
        <CardContent className="pt-2">
          <AttendanceTab studentId={studentProf.id} />
        </CardContent>
      </Card>

      {/* C. MARKS & GPA MARKS BREAKDOWN */}
      <Card className="rounded-3xl border-border/80 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Award className="h-4 w-4 text-brand-500" /> Marks, SGPA, CGPA &amp; Backlogs
              </CardTitle>
              <Badge variant="secondary" className="text-[10px] font-bold bg-slate-500/10 text-slate-700 border-slate-300">
                Managed by Academic Office
              </Badge>
            </div>
            <CardDescription className="text-xs">Semester wise SGPA, subjects, grades, and active backlog history</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs font-bold text-amber-700 border-amber-500/30 hover:bg-amber-500/10"
            onClick={() => openCorrectionModal('SGPA / CGPA / Backlogs', sgpaStat?.value || '')}
          >
            Request Correction
          </Button>
        </CardHeader>
        <CardContent className="pt-2">
          <AcademicsTab studentId={studentProf.id} />
        </CardContent>
      </Card>

      {/* D. ADMISSION MARKS & ENTRANCE RANKS */}
      <Card className="rounded-3xl border-border/80 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-500" /> Admission Scores &amp; Entrance Ranks
              </CardTitle>
              <Badge variant="secondary" className="text-[10px] font-bold bg-slate-500/10 text-slate-700 border-slate-300">
                Managed by Academic Office
              </Badge>
            </div>
            <CardDescription className="text-xs">SSC, Intermediate, EAMCET, and JEE ranks</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs font-bold text-amber-700 border-amber-500/30 hover:bg-amber-500/10"
            onClick={() => openCorrectionModal('Entrance & Admission Scores')}
          >
            Request Correction
          </Button>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
          <AcademicTile label="SSC Percentage" value={academic?.ssc_percentage ? `${academic.ssc_percentage}%` : 'N/A'} />
          <AcademicTile label="Intermediate %" value={academic?.intermediate_percentage ? `${academic.intermediate_percentage}%` : 'N/A'} />
          <AcademicTile label="EAMCET Rank" value={academic?.eamcet_rank ? String(academic.eamcet_rank) : 'N/A'} />
          <AcademicTile label="JEE Rank" value={academic?.jee_rank ? String(academic.jee_rank) : 'N/A'} />
        </CardContent>
      </Card>

      {/* CONTEXTUAL CORRECTION REQUEST MODAL */}
      <RequestCorrectionModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        sectionName={targetSection}
        currentValue={targetCurrVal}
      />
    </div>
  );
}

function AcademicTile({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="p-3 rounded-2xl bg-muted/20 border border-border/50">
      <span className="text-[10px] font-black uppercase text-muted-foreground block">{label}</span>
      <span className="text-xs font-bold text-foreground mt-0.5 block truncate">
        {value ? String(value) : 'Not specified'}
      </span>
    </div>
  );
}
