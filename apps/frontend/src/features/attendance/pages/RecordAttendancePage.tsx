import * as React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { attendanceService } from '../services/attendance.service';
import { adminService, Subject, Department, Section } from '@/features/admin/services/admin.service';
import { studentService, RosterStudent } from '@/features/students/services/student.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/shared/components/ui/Table';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { CheckCircle2, UserCheck, UserX, ShieldAlert, HeartPulse, Users, Calendar, UploadCloud } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'ON_DUTY' | 'MEDICAL_LEAVE';

const selectClass = 'w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring';

export function RecordAttendancePage() {
  const navigate = useNavigate();

  const [departmentId, setDepartmentId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [selectedSubjectId, setSelectedSubjectId] = React.useState('');
  const [attendanceDate, setAttendanceDate] = React.useState(new Date().toISOString().split('T')[0]);
  const [statusByStudent, setStatusByStudent] = React.useState<Record<string, AttendanceStatus>>({});
  const [feedbackMessage, setFeedbackMessage] = React.useState<string | null>(null);

  const { data: departments } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });

  const { data: sections } = useQuery<Section[]>({
    queryKey: ['admin', 'sections', departmentId],
    queryFn: () => adminService.getSections(departmentId),
    enabled: !!departmentId,
  });

  const { data: subjects, isLoading: subjectsLoading } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects', departmentId],
    queryFn: () => adminService.getSubjects(departmentId || undefined),
  });

  const { data: semesters } = useQuery({
    queryKey: ['admin', 'semesters'],
    queryFn: () => adminService.getSemesters(),
  });
  const currentSemester = semesters?.find((s) => s.is_current) ?? semesters?.[0];

  const {
    data: roster,
    isLoading: rosterLoading,
    isFetched: rosterFetched,
  } = useQuery<RosterStudent[]>({
    queryKey: ['students', 'roster', sectionId, currentSemester?.id],
    queryFn: () => studentService.getSectionRoster(sectionId, currentSemester!.id),
    enabled: !!sectionId && !!currentSemester?.id,
  });

  React.useEffect(() => {
    if (!roster) return;
    setStatusByStudent(Object.fromEntries(roster.map((s) => [s.id, 'PRESENT' as AttendanceStatus])));
  }, [roster]);

  const submitMutation = useMutation({
    mutationFn: () =>
      attendanceService.recordBulkAttendance({
        subject_id: selectedSubjectId,
        date: attendanceDate,
        records: Object.entries(statusByStudent).map(([student_id, status]) => ({ student_id, status })),
      }),
    onSuccess: () => {
      const presentCount = Object.values(statusByStudent).filter((s) => s === 'PRESENT' || s === 'ON_DUTY').length;
      const absentCount = Object.values(statusByStudent).length - presentCount;
      setFeedbackMessage(
        `Attendance recorded successfully for ${attendanceDate}. ${presentCount} Present/OD, ${absentCount} Absent.`
      );
      setTimeout(() => navigate('/dashboard'), 2500);
    },
    onError: (err: any) => {
      setFeedbackMessage(err?.response?.data?.error?.message || 'Failed to record attendance');
    },
  });

  const toggleStatus = (studentId: string, nextStatus: AttendanceStatus) => {
    setStatusByStudent((prev) => ({ ...prev, [studentId]: nextStatus }));
  };

  const markAllPresent = () => {
    setStatusByStudent((prev) => Object.fromEntries(Object.keys(prev).map((id) => [id, 'PRESENT' as AttendanceStatus])));
  };

  const canSubmit = !!selectedSubjectId && !!roster && roster.length > 0;

  const totalStudents = roster?.length ?? 0;
  const presentCount = Object.values(statusByStudent).filter((s) => s === 'PRESENT').length;

  return (
    <>
      <Breadcrumbs items={[{ label: 'Attendance' }, { label: 'Record Batch Attendance' }]} />

      <PageHeader
        title="Record Subject Attendance"
        subtitle="Select department, section, and subject to mark the active class roster"
        actions={
          <div className="flex gap-2">
            {roster && roster.length > 0 && (
              <Button variant="outline" size="sm" onClick={markAllPresent}>
                <UserCheck className="mr-1.5 h-4 w-4 text-emerald-600" /> Mark All Present
              </Button>
            )}
            <Button size="sm" onClick={() => navigate('/attendance/import')}>
              <UploadCloud className="mr-1.5 h-4 w-4" /> Bulk Excel Import
            </Button>
          </div>
        }
      />

      <div className="mt-6 space-y-6 max-w-4xl">
        {feedbackMessage && (
          <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs font-medium text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{feedbackMessage}</span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              1. Class Parameters
            </CardTitle>
            <CardDescription>Select target department and subject</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Department</label>
              <select className={selectClass} value={departmentId} onChange={(e) => { setDepartmentId(e.target.value); setSectionId(''); }}>
                <option value="">Select Dept...</option>
                {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Section</label>
              <select className={selectClass} value={sectionId} onChange={(e) => setSectionId(e.target.value)} disabled={!departmentId}>
                <option value="">Select Section...</option>
                {sections?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Subject</label>
              {subjectsLoading ? (
                <Skeleton className="h-10 w-full rounded-lg" />
              ) : (
                <select className={selectClass} value={selectedSubjectId} onChange={(e) => setSelectedSubjectId(e.target.value)}>
                  <option value="">Select Subject...</option>
                  {subjects?.map((sub) => <option key={sub.id} value={sub.id}>{sub.code} — {sub.name}</option>)}
                </select>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Date</label>
              <input
                type="date"
                value={attendanceDate}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className="w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base">2. Enrolled Student Roster</CardTitle>
              <CardDescription>Toggle attendance status per student</CardDescription>
            </div>
            {totalStudents > 0 && (
              <Badge variant="success" dot>
                {presentCount} / {totalStudents} Present ({Math.round((presentCount / totalStudents) * 100)}%)
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            {!sectionId ? (
              <EmptyState icon={Users} title="Select a section" description="Select a department and section above to display enrolled students." />
            ) : rosterLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-12 w-full rounded-xl" />
                <Skeleton className="h-12 w-full rounded-xl" />
                <Skeleton className="h-12 w-full rounded-xl" />
              </div>
            ) : rosterFetched && (!roster || roster.length === 0) ? (
              <EmptyState icon={Users} title="No students enrolled" description="This section has no registered students for the current semester." />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Roll Number</TableHead>
                    <TableHead>Student Name</TableHead>
                    <TableHead className="text-right">Attendance Mark</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roster!.map((student) => (
                    <TableRow key={student.id}>
                      <TableCell className="font-mono font-bold text-primary">{student.roll_number}</TableCell>
                      <TableCell className="font-semibold">{student.full_name}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {([
                            ['PRESENT', UserCheck, 'bg-emerald-600 hover:bg-emerald-700 text-white'],
                            ['ABSENT', UserX, 'bg-rose-600 hover:bg-rose-700 text-white'],
                            ['ON_DUTY', ShieldAlert, 'bg-sky-600 hover:bg-sky-700 text-white'],
                            ['MEDICAL_LEAVE', HeartPulse, 'bg-amber-600 hover:bg-amber-700 text-white'],
                          ] as const).map(([value, Icon, activeClass]) => {
                            const isSelected = statusByStudent[student.id] === value;
                            return (
                              <button
                                key={value}
                                type="button"
                                onClick={() => toggleStatus(student.id, value)}
                                className={cn(
                                  'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer select-none',
                                  isSelected
                                    ? activeClass
                                    : 'bg-muted/80 text-muted-foreground hover:bg-accent hover:text-foreground'
                                )}
                              >
                                <Icon className="h-3.5 w-3.5" />
                                <span>{value === 'ON_DUTY' ? 'OD' : value === 'MEDICAL_LEAVE' ? 'Medical' : value.charAt(0) + value.slice(1).toLowerCase()}</span>
                              </button>
                            );
                          })}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>

          {roster && roster.length > 0 && (
            <div className="p-4 border-t border-border/80 bg-muted/20 flex justify-end">
              <Button onClick={() => submitMutation.mutate()} isLoading={submitMutation.isPending} disabled={!canSubmit} size="lg">
                Submit Attendance Batch
              </Button>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
