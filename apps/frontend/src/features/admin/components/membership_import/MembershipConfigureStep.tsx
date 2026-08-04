import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Modal } from '@/shared/components/ui/Modal';
import { adminService } from '../../services/admin.service';
import type {
  MembershipImportConfiguration,
  MembershipImportPreview,
} from '../../services/membershipImport.service';

const SELECT_CLASS =
  'h-10 w-full rounded-xl border border-input bg-background/60 px-3 text-xs font-semibold shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring';

interface MembershipConfigureStepProps {
  preview: MembershipImportPreview;
  onBack: () => void;
  onStart: (config: MembershipImportConfiguration) => void;
  isStarting: boolean;
  startError: string | null;
}

export function MembershipConfigureStep({
  preview,
  onBack,
  onStart,
  isStarting,
  startError,
}: MembershipConfigureStepProps) {
  const { data: departments, isLoading: loadingDepartments } = useQuery({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });
  const { data: semesters, isLoading: loadingSemesters } = useQuery({
    queryKey: ['admin', 'semesters'],
    queryFn: adminService.getSemesters,
  });
  const { data: academicYears, isLoading: loadingYears } = useQuery({
    queryKey: ['admin', 'academic-years'],
    queryFn: adminService.getAcademicYears,
  });

  const [departmentId, setDepartmentId] = React.useState('');
  const [semesterId, setSemesterId] = React.useState('');
  const [academicYearId, setAcademicYearId] = React.useState('');
  const [sectionName, setSectionName] = React.useState('A');
  const [batchYear, setBatchYear] = React.useState(new Date().getFullYear().toString());
  const [studyYear, setStudyYear] = React.useState('1');
  const [reassign, setReassign] = React.useState(false);
  const [touched, setTouched] = React.useState(false);
  const [showConfirmModal, setShowConfirmModal] = React.useState(false);

  // Set defaults once options load
  React.useEffect(() => {
    if (departments && departments.length > 0 && !departmentId) {
      setDepartmentId(departments[0].id);
    }
    if (semesters && semesters.length > 0 && !semesterId) {
      setSemesterId(semesters[0].id);
    }
    if (academicYears && academicYears.length > 0 && !academicYearId) {
      const current = academicYears.find((ay) => ay.is_current) ?? academicYears[0];
      setAcademicYearId(current.id);
    }
  }, [departments, semesters, academicYears, departmentId, semesterId, academicYearId]);

  const departmentValid = Boolean(departmentId);
  const semesterValid = Boolean(semesterId);
  const sectionValid = Boolean(sectionName.trim());
  const batchYearNum = parseInt(batchYear, 10);
  const batchValid = !isNaN(batchYearNum) && batchYearNum >= 2000 && batchYearNum <= 2100;
  const formValid = departmentValid && semesterValid && sectionValid && batchValid;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!formValid) return;
    setShowConfirmModal(true);
  };

  const confirmAndStart = () => {
    setShowConfirmModal(false);
    onStart({
      department_id: departmentId,
      semester_id: semesterId,
      section_name: sectionName.trim().toUpperCase(),
      batch_year: batchYearNum,
      academic_year_id: academicYearId || null,
      study_year: studyYear ? parseInt(studyYear, 10) : null,
      reassign_existing_students: reassign,
    });
  };

  const isLoadingCatalog = loadingDepartments || loadingSemesters || loadingYears;

  if (isLoadingCatalog) {
    return <Skeleton className="h-96 w-full rounded-2xl" />;
  }

  const { summary } = preview;

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              Academic & Assignment Configuration
            </CardTitle>
            <CardDescription>
              Select the department, semester, and section to associate with new student accounts and counselor assignments.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {/* Department */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">
                  Department <span className="text-rose-500">*</span>
                </label>
                <select
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                  className={SELECT_CLASS}
                >
                  <option value="" disabled>Select department…</option>
                  {departments?.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} — {d.name}
                    </option>
                  ))}
                </select>
                {touched && !departmentValid && (
                  <p className="text-[11px] font-medium text-rose-600">Department is required.</p>
                )}
              </div>

              {/* Semester */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">
                  Semester <span className="text-rose-500">*</span>
                </label>
                <select
                  value={semesterId}
                  onChange={(e) => setSemesterId(e.target.value)}
                  className={SELECT_CLASS}
                >
                  <option value="" disabled>Select semester…</option>
                  {semesters?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                {touched && !semesterValid && (
                  <p className="text-[11px] font-medium text-rose-600">Semester is required.</p>
                )}
              </div>

              {/* Section Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">
                  Section Name <span className="text-rose-500">*</span>
                </label>
                <Input
                  value={sectionName}
                  onChange={(e) => setSectionName(e.target.value)}
                  placeholder="e.g. A, B, CSE-A"
                  maxLength={20}
                  className="h-10"
                />
                {touched && !sectionValid && (
                  <p className="text-[11px] font-medium text-rose-600">Section name is required.</p>
                )}
              </div>

              {/* Batch Year */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">
                  Batch Year <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  value={batchYear}
                  onChange={(e) => setBatchYear(e.target.value)}
                  placeholder="e.g. 2023"
                  min={2000}
                  max={2100}
                  className="h-10"
                />
                {touched && !batchValid && (
                  <p className="text-[11px] font-medium text-rose-600">Enter a valid batch year (2000–2100).</p>
                )}
              </div>

              {/* Academic Year */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">Academic Session</label>
                <select
                  value={academicYearId}
                  onChange={(e) => setAcademicYearId(e.target.value)}
                  className={SELECT_CLASS}
                >
                  <option value="">(Optional) None selected</option>
                  {academicYears?.map((ay) => (
                    <option key={ay.id} value={ay.id}>
                      {ay.name} {ay.is_current ? '(Current)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Study Year */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">Study Year (1–4)</label>
                <select
                  value={studyYear}
                  onChange={(e) => setStudyYear(e.target.value)}
                  className={SELECT_CLASS}
                >
                  <option value="1">1st Year</option>
                  <option value="2">2nd Year</option>
                  <option value="3">3rd Year</option>
                  <option value="4">4th Year</option>
                </select>
              </div>
            </div>

            {/* Reassignment Option */}
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reassign}
                  onChange={(e) => setReassign(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-primary"
                />
                <div>
                  <span className="text-xs font-bold text-foreground">
                    Reassign existing students to new counselor
                  </span>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    If checked, students who are currently assigned to another counselor will have their existing assignment ended and will be reassigned to the counselor specified in this import.
                  </p>
                </div>
              </label>
            </div>

            {startError && (
              <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
                <p className="text-xs text-rose-700 dark:text-rose-300">{startError}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Buttons */}
        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={onBack} disabled={isStarting}>
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Back to Preview
          </Button>
          <Button type="submit" size="lg" disabled={isStarting}>
            <Play className="mr-1.5 h-4 w-4 fill-current" /> Review & Confirm Import
          </Button>
        </div>
      </form>

      {/* Confirmation Modal */}
      <Modal
        open={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Confirm Membership Import Execution"
        description="Please review the import scope and actions before committing to the database."
        className="max-w-xl"
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 flex items-start gap-2.5">
            <ShieldCheck className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 dark:text-amber-300">
              <p className="font-bold">Single Transaction Execution</p>
              <p className="mt-0.5">
                The import executes in a single database transaction. If any unhandled error occurs, all changes will be completely rolled back.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Execution Impact Summary
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">Total Students:</span>
                <span className="ml-1.5 font-bold text-foreground">{summary.total_students}</span>
              </div>
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">New Student Accounts:</span>
                <span className="ml-1.5 font-bold text-emerald-600 dark:text-emerald-400">
                  {summary.new_student_accounts}
                </span>
              </div>
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">Existing Account Reuse:</span>
                <span className="ml-1.5 font-bold text-foreground">{summary.existing_student_accounts}</span>
              </div>
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">Counselors Found:</span>
                <span className="ml-1.5 font-bold text-foreground">{summary.existing_counselor_accounts}</span>
              </div>
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">New Memberships:</span>
                <span className="ml-1.5 font-bold text-primary">{summary.new_memberships}</span>
              </div>
              <div className="rounded-lg bg-muted/40 p-2.5">
                <span className="text-muted-foreground">Reassignment Enabled:</span>
                <span className="ml-1.5 font-bold text-foreground">{reassign ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          {summary.missing_counselors > 0 && (
            <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-700 dark:text-rose-300">
              <span className="font-bold">{summary.missing_counselors} counselor(s) missing:</span> Students mapped to missing counselors will be skipped.
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-border">
            <Button variant="outline" size="sm" onClick={() => setShowConfirmModal(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={confirmAndStart} disabled={isStarting}>
              {isStarting ? (
                <>
                  <div className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Starting…
                </>
              ) : (
                'Confirm & Start Import'
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
