import * as React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { attendanceService } from '../services/attendance.service';
import { adminService, Subject } from '@/features/admin/services/admin.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { CheckCircle2, UserCheck, UserX, ShieldAlert, HeartPulse } from 'lucide-react';

interface MockStudentRow {
  student_id: string;
  roll_number: string;
  name: string;
  status: 'PRESENT' | 'ABSENT' | 'ON_DUTY' | 'MEDICAL_LEAVE';
}

export function RecordAttendancePage() {
  const navigate = useNavigate();

  const [selectedSubjectId, setSelectedSubjectId] = React.useState<string>('');
  const [attendanceDate, setAttendanceDate] = React.useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [students, setStudents] = React.useState<MockStudentRow[]>([
    { student_id: 'stu-1', roll_number: '21CS101', name: 'Arjun Kumar', status: 'PRESENT' },
    { student_id: 'stu-2', roll_number: '21CS102', name: 'Priya Sharma', status: 'PRESENT' },
    { student_id: 'stu-3', roll_number: '21CS103', name: 'Rahul Verma', status: 'PRESENT' },
    { student_id: 'stu-4', roll_number: '21CS104', name: 'Sneha Patel', status: 'PRESENT' },
    { student_id: 'stu-5', roll_number: '21CS105', name: 'Vikram Singh', status: 'PRESENT' },
  ]);

  const [feedbackMessage, setFeedbackMessage] = React.useState<string | null>(null);

  const { data: subjects, isLoading: subjectsLoading } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects'],
    queryFn: () => adminService.getSubjects(),
  });

  const submitMutation = useMutation({
    mutationFn: () =>
      attendanceService.recordBulkAttendance({
        subject_id: selectedSubjectId,
        date: attendanceDate,
        records: students.map((s) => ({ student_id: s.student_id, status: s.status })),
      }),
    onSuccess: () => {
      const presentCount = students.filter((s) => s.status === 'PRESENT' || s.status === 'ON_DUTY').length;
      const absentCount = students.length - presentCount;
      setFeedbackMessage(
        `Attendance recorded successfully for ${attendanceDate}. ${presentCount} Present/OD, ${absentCount} Absent.`
      );
      setTimeout(() => navigate('/dashboard'), 2500);
    },
    onError: (err: any) => {
      setFeedbackMessage(err?.response?.data?.error?.message || 'Failed to record attendance');
    },
  });

  const toggleStatus = (studentId: string, nextStatus: 'PRESENT' | 'ABSENT' | 'ON_DUTY' | 'MEDICAL_LEAVE') => {
    setStudents((prev) =>
      prev.map((s) => (s.student_id === studentId ? { ...s, status: nextStatus } : s))
    );
  };

  const markAllPresent = () => {
    setStudents((prev) => prev.map((s) => ({ ...s, status: 'PRESENT' })));
  };

  return (
    <AppShell userRole="FACULTY" userName="Prof. Rajesh Kumar">
      <Breadcrumbs items={[{ label: 'Attendance', href: '/attendance' }, { label: 'Record Attendance' }]} />

      <PageHeader
        title="Record Subject Attendance"
        subtitle="3-Click Fast Entry Flow — Default: All Present (§21.2)"
        actions={
          <Button variant="outline" size="sm" onClick={markAllPresent}>
            <UserCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" /> Mark All Present
          </Button>
        }
      />

      <div className="mt-6 space-y-6 max-w-4xl">
        {feedbackMessage && (
          <div className="flex items-center gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-4 text-xs font-medium text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-300 animate-in fade-in-50">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{feedbackMessage}</span>
          </div>
        )}

        {/* Step 1 & 2: Select Subject & Date */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Step 1: Select Subject & Date</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Subject</label>
              {subjectsLoading ? (
                <Skeleton className="h-9 w-full" />
              ) : (
                <select
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="w-full h-9 rounded-md border bg-transparent px-3 text-xs focus:ring-1 focus:ring-ring"
                >
                  <option value="">Select a subject...</option>
                  {subjects?.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.code} — {sub.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Class Date</label>
              <input
                type="date"
                value={attendanceDate}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className="w-full h-9 rounded-md border bg-transparent px-3 text-xs"
              />
            </div>
          </CardContent>
        </Card>

        {/* Step 3: Student List Exceptions Toggle */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Step 2: Class Roster Exceptions</CardTitle>
            <span className="text-xs text-muted-foreground">
              {students.filter((s) => s.status === 'PRESENT').length} / {students.length} Present
            </span>
          </CardHeader>
          <CardContent className="divide-y divide-border">
            {students.map((student) => (
              <div key={student.student_id} className="py-3 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs font-bold text-primary mr-3">{student.roll_number}</span>
                  <span className="text-sm font-medium">{student.name}</span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => toggleStatus(student.student_id, 'PRESENT')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1 ${
                      student.status === 'PRESENT'
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-muted text-muted-foreground hover:bg-accent'
                    }`}
                  >
                    <UserCheck className="h-3 w-3" /> Present
                  </button>

                  <button
                    type="button"
                    onClick={() => toggleStatus(student.student_id, 'ABSENT')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1 ${
                      student.status === 'ABSENT'
                        ? 'bg-red-600 text-white shadow-xs'
                        : 'bg-muted text-muted-foreground hover:bg-accent'
                    }`}
                  >
                    <UserX className="h-3 w-3" /> Absent
                  </button>

                  <button
                    type="button"
                    onClick={() => toggleStatus(student.student_id, 'ON_DUTY')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1 ${
                      student.status === 'ON_DUTY'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-muted text-muted-foreground hover:bg-accent'
                    }`}
                  >
                    <ShieldAlert className="h-3 w-3" /> OD
                  </button>

                  <button
                    type="button"
                    onClick={() => toggleStatus(student.student_id, 'MEDICAL_LEAVE')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1 ${
                      student.status === 'MEDICAL_LEAVE'
                        ? 'bg-amber-600 text-white shadow-xs'
                        : 'bg-muted text-muted-foreground hover:bg-accent'
                    }`}
                  >
                    <HeartPulse className="h-3 w-3" /> Medical
                  </button>
                </div>
              </div>
            ))}
          </CardContent>
          <div className="p-4 border-t bg-muted/20 flex justify-end">
            <Button
              onClick={() => submitMutation.mutate()}
              disabled={!selectedSubjectId || submitMutation.isPending}
              size="lg"
            >
              {submitMutation.isPending ? 'Submitting Attendance...' : 'Submit Attendance (3rd Click)'}
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
