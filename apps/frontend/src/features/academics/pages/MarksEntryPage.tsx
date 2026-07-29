import * as React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { academicsService } from '../services/academics.service';
import { adminService, Subject, Department, Section, Semester } from '@/features/admin/services/admin.service';
import { studentService, RosterStudent } from '@/features/students/services/student.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/shared/components/ui/Table';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { CheckCircle2, Users, Award } from 'lucide-react';

const selectClass = 'w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring';
const ASSESSMENT_TYPES = ['MID_TERM_1', 'MID_TERM_2', 'INTERNAL', 'EXTERNAL'];

export function MarksEntryPage() {
  const navigate = useNavigate();

  const [departmentId, setDepartmentId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [semesterId, setSemesterId] = React.useState('');
  const [selectedSubjectId, setSelectedSubjectId] = React.useState('');
  const [assessmentType, setAssessmentType] = React.useState(ASSESSMENT_TYPES[0]);
  const [maxMarks, setMaxMarks] = React.useState(30);
  const [marksByStudent, setMarksByStudent] = React.useState<Record<string, number>>({});
  const [feedbackMsg, setFeedbackMsg] = React.useState<string | null>(null);

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

  const { data: semesters } = useQuery<Semester[]>({
    queryKey: ['admin', 'semesters'],
    queryFn: () => adminService.getSemesters(),
  });

  React.useEffect(() => {
    if (!semesterId && semesters && semesters.length > 0) {
      setSemesterId((semesters.find((s) => s.is_current) ?? semesters[0]).id);
    }
  }, [semesters, semesterId]);

  const {
    data: roster,
    isLoading: rosterLoading,
    isFetched: rosterFetched,
  } = useQuery<RosterStudent[]>({
    queryKey: ['students', 'roster', sectionId, semesterId],
    queryFn: () => studentService.getSectionRoster(sectionId, semesterId),
    enabled: !!sectionId && !!semesterId,
  });

  React.useEffect(() => {
    if (!roster) return;
    setMarksByStudent(Object.fromEntries(roster.map((s) => [s.id, 0])));
  }, [roster]);

  const submitMutation = useMutation({
    mutationFn: () =>
      academicsService.recordBulkMarks({
        subject_id: selectedSubjectId,
        semester_id: semesterId,
        assessment_type: assessmentType,
        records: Object.entries(marksByStudent).map(([student_id, marks_obtained]) => ({
          student_id,
          marks_obtained,
          max_marks: maxMarks,
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
    setMarksByStudent((prev) => ({ ...prev, [studentId]: value }));
  };

  const canSubmit = !!selectedSubjectId && !!semesterId && !!roster && roster.length > 0;

  return (
    <>
      <Breadcrumbs items={[{ label: 'Academics' }, { label: 'Marks Entry' }]} />

      <PageHeader
        title="Faculty Marks & Assessment Entry"
        subtitle="Record assessment scores and publish grades to student academic records"
      />

      <div className="mt-6 space-y-6 max-w-4xl">
        {feedbackMsg && (
          <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs font-medium text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{feedbackMsg}</span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="h-4 w-4 text-primary" />
              1. Assessment Selection
            </CardTitle>
            <CardDescription>Select class section and exam type</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
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
              <label className="text-xs font-semibold text-foreground">Assessment Type</label>
              <select className={selectClass} value={assessmentType} onChange={(e) => setAssessmentType(e.target.value)}>
                {ASSESSMENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Semester</label>
              <select className={selectClass} value={semesterId} onChange={(e) => setSemesterId(e.target.value)}>
                <option value="">Select Semester...</option>
                {semesters?.map((s) => <option key={s.id} value={s.id}>{s.name}{s.is_current ? ' (Active)' : ''}</option>)}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Max Marks</label>
              <Input type="number" min={1} value={maxMarks} onChange={(e) => setMaxMarks(Number(e.target.value))} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">2. Enrolled Student Roster Marks</CardTitle>
            <CardDescription>Enter marks obtained out of {maxMarks}</CardDescription>
          </CardHeader>
          <CardContent>
            {!sectionId || !semesterId ? (
              <EmptyState icon={Users} title="Select class section" description="Select department, section, and semester above to display roster." />
            ) : rosterLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-12 w-full rounded-xl" />
                <Skeleton className="h-12 w-full rounded-xl" />
              </div>
            ) : rosterFetched && (!roster || roster.length === 0) ? (
              <EmptyState icon={Users} title="No students enrolled" description="This section has no students registered for the selected term." />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Roll Number</TableHead>
                    <TableHead>Student Name</TableHead>
                    <TableHead className="text-right">Marks Obtained / Max</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roster!.map((student) => (
                    <TableRow key={student.id}>
                      <TableCell className="font-mono font-bold text-primary">{student.roll_number}</TableCell>
                      <TableCell className="font-semibold">{student.full_name}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Input
                            type="number"
                            min={0}
                            max={maxMarks}
                            value={marksByStudent[student.id] ?? 0}
                            onChange={(e) => handleMarkChange(student.id, Number(e.target.value))}
                            className="w-24 text-right font-mono font-bold"
                          />
                          <span className="text-xs text-muted-foreground font-mono">/ {maxMarks}</span>
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
                Publish Marks Batch
              </Button>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
