import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Play, Sparkles, Info, AlertCircle, FileSearch, Hash } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { adminService } from '../../services/admin.service';
import type { ImportConfiguration, ImportPreview, SuggestionSource } from '../../services/import.service';
import { cn } from '@/shared/utils/cn';

const SOURCE_COPY: Record<SuggestionSource, { label: string; tone: 'success' | 'info' | 'warning' | 'secondary' }> = {
  FILE: { label: 'From the file', tone: 'success' },
  DERIVED: { label: 'From the roll number', tone: 'info' },
  CURRENT: { label: 'Current academic setting', tone: 'info' },
  NONE: { label: 'Not found — please choose', tone: 'warning' },
};

const SELECT_CLASS =
  'h-10 w-full rounded-xl border border-input bg-background/60 px-3 text-xs font-semibold shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring';

interface ConfigureStepProps {
  preview: ImportPreview;
  onBack: () => void;
  onStart: (config: ImportConfiguration) => void;
  isStarting: boolean;
  startError: string | null;
}

export function ConfigureStep({ preview, onBack, onStart, isStarting, startError }: ConfigureStepProps) {
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

  const suggestionFor = React.useCallback(
    (field: string) => preview.suggestions.find((s) => s.field === field),
    [preview.suggestions]
  );

  const [departmentId, setDepartmentId] = React.useState('');
  const [semesterId, setSemesterId] = React.useState('');
  const [academicYearId, setAcademicYearId] = React.useState('');
  const [sectionName, setSectionName] = React.useState('');
  const [batchYear, setBatchYear] = React.useState('');
  const [studyYear, setStudyYear] = React.useState('');
  const [reassign, setReassign] = React.useState(false);
  const [touched, setTouched] = React.useState(false);

  // Prefill once the suggestions and the catalog lists are both in hand — a
  // detected id is only useful if it still exists in the dropdown behind it.
  React.useEffect(() => {
    setDepartmentId((current) => current || suggestionFor('department_id')?.detected_id || '');
    setSemesterId((current) => current || suggestionFor('semester_id')?.detected_id || '');
    setAcademicYearId((current) => current || suggestionFor('academic_year_id')?.detected_id || '');
    setSectionName((current) => current || suggestionFor('section_name')?.detected_value || '');
    setBatchYear((current) => current || suggestionFor('batch_year')?.detected_value || '');
  }, [suggestionFor]);

  // The study year follows the semester: 4-1 and 4-2 both mean fourth year.
  React.useEffect(() => {
    const semester = semesters?.find((s) => s.id === semesterId);
    if (semester) setStudyYear(String(Math.ceil(semester.number / 2)));
  }, [semesterId, semesters]);

  const isLoading = loadingDepartments || loadingSemesters || loadingYears;
  const parsedBatchYear = Number.parseInt(batchYear, 10);
  const batchYearValid = Number.isFinite(parsedBatchYear) && parsedBatchYear >= 2000 && parsedBatchYear <= 2100;
  const canStart = Boolean(departmentId && semesterId && sectionName.trim() && batchYearValid);

  const handleStart = () => {
    setTouched(true);
    if (!canStart) return;
    onStart({
      department_id: departmentId,
      semester_id: semesterId,
      section_name: sectionName.trim().toUpperCase(),
      batch_year: parsedBatchYear,
      academic_year_id: academicYearId || null,
      study_year: studyYear ? Number.parseInt(studyYear, 10) : null,
      reassign_existing_students: reassign,
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3 rounded-xl border border-sky-500/20 bg-sky-500/10 p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-600 dark:text-sky-400" />
        <div className="text-xs leading-relaxed text-sky-800 dark:text-sky-200">
          <p className="font-bold">These values apply to all {preview.importable_students} students in this import.</p>
          <p className="mt-0.5 font-medium">
            Anything the file already told us is filled in below and labelled with where it came from. Check it and
            change what needs changing.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-4 w-4 text-primary" />
            Academic placement
          </CardTitle>
          <CardDescription>
            Every generated student is enrolled here and assigned the counsellor named against their roll number.
          </CardDescription>
        </CardHeader>

        <CardContent className="grid gap-5 md:grid-cols-2">
          <Field
            label="Department"
            required
            suggestion={suggestionFor('department_id')}
            error={touched && !departmentId ? 'Choose the department these students belong to.' : null}
          >
            <select
              className={SELECT_CLASS}
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
            >
              <option value="">Select a department…</option>
              {departments?.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.code} — {department.name}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label="Semester"
            required
            suggestion={suggestionFor('semester_id')}
            error={touched && !semesterId ? 'Choose the semester these students are entering.' : null}
          >
            <select className={SELECT_CLASS} value={semesterId} onChange={(e) => setSemesterId(e.target.value)}>
              <option value="">Select a semester…</option>
              {semesters?.map((semester) => (
                <option key={semester.id} value={semester.id}>
                  {semester.name}
                  {semester.is_current ? ' (current)' : ''}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label="Section"
            required
            suggestion={suggestionFor('section_name')}
            hint="Created automatically if it does not exist yet for this department, year and batch."
            error={touched && !sectionName.trim() ? 'Enter the section, for example A.' : null}
          >
            <Input
              value={sectionName}
              onChange={(e) => setSectionName(e.target.value.toUpperCase())}
              placeholder="A"
              maxLength={20}
              error={touched && !sectionName.trim()}
            />
          </Field>

          <Field
            label="Batch"
            required
            suggestion={suggestionFor('batch_year')}
            error={touched && !batchYearValid ? 'Enter the four-digit admission year, for example 2023.' : null}
          >
            <Input
              type="number"
              inputMode="numeric"
              value={batchYear}
              onChange={(e) => setBatchYear(e.target.value)}
              placeholder="2023"
              min={2000}
              max={2100}
              error={touched && !batchYearValid}
            />
          </Field>

          <Field label="Academic Year" suggestion={suggestionFor('academic_year_id')}>
            <select
              className={SELECT_CLASS}
              value={academicYearId}
              onChange={(e) => setAcademicYearId(e.target.value)}
            >
              <option value="">Not set</option>
              {academicYears?.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                  {year.is_current ? ' (current)' : ''}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Study year" hint="Follows the semester. Used to group the section in Academic Configuration.">
            <div className="flex h-10 items-center gap-2 rounded-xl border border-border/70 bg-muted/40 px-3.5">
              <Hash className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="text-xs font-bold text-foreground">
                {studyYear ? `Year ${studyYear}` : 'Select a semester first'}
              </span>
            </div>
          </Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Existing students</CardTitle>
          <CardDescription>
            {preview.duplicate_students > 0
              ? `${preview.duplicate_students} roll number${preview.duplicate_students === 1 ? '' : 's'} in this file already have an account.`
              : 'No roll number in this file already has an account.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <label
            className={cn(
              'flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition-all',
              reassign ? 'border-primary/40 bg-primary/5' : 'border-border/70 bg-background/40 hover:bg-accent/40'
            )}
          >
            <input
              type="checkbox"
              checked={reassign}
              onChange={(e) => setReassign(e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-brand-600"
            />
            <span className="min-w-0">
              <span className="block text-xs font-bold text-foreground">
                Move existing students onto the counsellor named in this file
              </span>
              <span className="mt-1 block text-[11px] font-medium leading-relaxed text-muted-foreground">
                Off by default. Their account, history and marks are untouched either way — this only closes the
                current counsellor assignment and opens a new one. Leave it off unless this sheet is a
                re-allotment.
              </span>
            </span>
          </label>
        </CardContent>
      </Card>

      {startError && (
        <div className="flex items-start gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <p className="text-xs font-medium leading-relaxed text-rose-700 dark:text-rose-300">{startError}</p>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/80 pt-5">
        <Button variant="outline" onClick={onBack} disabled={isStarting}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Back to preview
        </Button>
        <div className="flex items-center gap-3">
          {!canStart && touched && (
            <span className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">
              Fill in the highlighted fields
            </span>
          )}
          <Button size="lg" onClick={handleStart} isLoading={isStarting}>
            <Play className="mr-1.5 h-4 w-4" />
            Import {preview.importable_students} student{preview.importable_students === 1 ? '' : 's'}
          </Button>
        </div>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string | null;
  suggestion?: { source: SuggestionSource; note?: string | null; detected_value?: string | null };
  children: React.ReactNode;
}

function Field({ label, required, hint, error, suggestion, children }: FieldProps) {
  const copy = suggestion ? SOURCE_COPY[suggestion.source] : null;

  return (
    <div className="space-y-1.5">
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
          {label}
          {required && <span className="ml-1 text-rose-500">*</span>}
        </label>
        {copy && (
          <Badge variant={copy.tone} className="text-[9px]">
            <Sparkles className="h-2.5 w-2.5" />
            {copy.label}
          </Badge>
        )}
      </div>

      {children}

      {error ? (
        <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">{error}</p>
      ) : (
        (suggestion?.note || hint) && (
          <p className="text-[11px] font-medium leading-relaxed text-muted-foreground">{suggestion?.note || hint}</p>
        )
      )}
    </div>
  );
}
