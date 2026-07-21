import * as React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { academicsService } from '../services/academics.service';
import { adminService, Subject } from '@/features/admin/services/admin.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { CheckCircle2 } from 'lucide-react';

interface MockStudentMarkRow {
  student_id: string;
  roll_number: string;
  name: string;
  marks_obtained: number;
  max_marks: number;
}

export function MarksEntryPage() {
  const navigate = useNavigate();

  const [selectedSubjectId, setSelectedSubjectId] = React.useState<string>('');
  const [assessmentType, setAssessmentType] = React.useState<string>('MID_TERM_1');
  const [semesterId, setSemesterId] = React.useState<string>('sem-5');
  const [feedbackMsg, setFeedbackMsg] = React.useState<string | null>(null);

  const [students, setStudents] = React.useState<MockStudentMarkRow[]>([
    { student_id: 'stu-1', roll_number: '21CS101', name: 'Arjun Kumar', marks_obtained: 24, max_marks: 30 },
    { student_id: 'stu-2', roll_number: '21CS102', name: 'Priya Sharma', marks_obtained: 28, max_marks: 30 },
    { student_id: 'stu-3', roll_number: '21CS103', name: 'Rahul Verma', marks_obtained: 18, max_marks: 30 },
    { student_id: 'stu-4', roll_number: '21CS104', name: 'Sneha Patel', marks_obtained: 26, max_marks: 30 },
    { student_id: 'stu-5', roll_number: '21CS105', name: 'Vikram Singh', marks_obtained: 22, max_marks: 30 },
  ]);

  const { data: subjects, isLoading: subjectsLoading } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects'],
    queryFn: () => adminService.getSubjects(),
  });

  const submitMutation = useMutation({
    mutationFn: () =>
      academicsService.recordBulkMarks({
        subject_id: selectedSubjectId,
        semester_id: semesterId,
        assessment_type: assessmentType,
        records: students.map((s) => ({
          student_id: s.student_id,
          marks_obtained: s.marks_obtained,
          max_marks: s.max_marks,
        })),
      }),
    onSuccess: () => {
      setFeedbackMsg(`Marks recorded successfully for ${assessmentType}.`);
      setTimeout(() => navigate('/dashboard'), 2500);
    },
    onError: (err: any) => {
      setFeedbackMsg(err?.response?.data?.error?.message || 'Failed to record marks.');
    },
  });

  const handleMarkChange = (studentId: string, value: number) => {
    setStudents((prev) =>
      prev.map((s) => (s.student_id === studentId ? { ...s, marks_obtained: value } : s))
    );
  };

  return (
    <AppShell userRole="FACULTY" userName="Prof. Rajesh Kumar">
      <Breadcrumbs items={[{ label: 'Academics', href: '/academics' }, { label: 'Marks Entry' }]} />

      <PageHeader
        title="Faculty Marks Entry"
        subtitle="Record Mid-Term, Internal, or External exam marks with validation (§22)"
      />

      <div className="mt-6 space-y-6 max-w-4xl">
        {feedbackMsg && (
          <div className="flex items-center gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-4 text-xs font-medium text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{feedbackMsg}</span>
          </div>
        )}

        {/* Assessment & Subject Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subject & Assessment Selection</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                  <option value="">Select subject...</option>
                  {subjects?.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.code} — {sub.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Assessment Type</label>
              <select
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value)}
                className="w-full h-9 rounded-md border bg-transparent px-3 text-xs"
              >
                <option value="MID_TERM_1">MID_TERM_1 (Max: 30)</option>
                <option value="MID_TERM_2">MID_TERM_2 (Max: 30)</option>
                <option value="INTERNAL">INTERNAL (Max: 20)</option>
                <option value="EXTERNAL">EXTERNAL (Max: 50)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Semester</label>
              <select
                value={semesterId}
                onChange={(e) => setSemesterId(e.target.value)}
                className="w-full h-9 rounded-md border bg-transparent px-3 text-xs"
              >
                <option value="sem-5">Semester 5 (Current)</option>
                <option value="sem-4">Semester 4</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Student Marks List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Student Class List</CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-border">
            {students.map((student) => (
              <div key={student.student_id} className="py-3 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs font-bold text-primary mr-3">{student.roll_number}</span>
                  <span className="text-sm font-medium">{student.name}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={student.max_marks}
                    value={student.marks_obtained}
                    onChange={(e) => handleMarkChange(student.student_id, Number(e.target.value))}
                    className="w-24 text-right"
                  />
                  <span className="text-xs text-muted-foreground">/ {student.max_marks}</span>
                </div>
              </div>
            ))}
          </CardContent>
          <div className="p-4 border-t bg-muted/20 flex justify-end">
            <Button
              onClick={() => submitMutation.mutate()}
              disabled={!selectedSubjectId || submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Saving Marks...' : 'Save & Publish Marks'}
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
