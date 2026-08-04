import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  X,
  Download,
  Award,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { adminService, Subject, Department, Section, Semester, AcademicYear } from '@/features/admin/services/admin.service';
import { cn } from '@/shared/utils/cn';
import { marksImportService, AssessmentTemplate } from '../../services/marksImport.service';

const ACCEPTED = '.xlsx,.xlsm,.xls,.csv';
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm', '.xls', '.csv'];

const SELECT_CLASS =
  'h-10 w-full rounded-xl border border-input bg-background/60 px-3 text-xs font-semibold shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring';

const ASSESSMENT_CATEGORIES = [
  { code: 'MID_WRITTEN', label: 'Mid Written Exam (Q_A, Q_B, Q_C, Q_D)' },
  { code: 'OPEN_BOOK', label: 'Open Book Exam (20 Marks)' },
  { code: 'OBJECTIVE_TEST', label: 'Objective Test (20 Marks)' },
  { code: 'SEMINAR', label: 'Seminar (5 Marks)' },
  { code: 'ASSIGNMENT', label: 'Assignment (10 Marks)' },
  { code: 'QUIZ', label: 'Quiz (10 Marks)' },
  { code: 'LAB_INTERNAL', label: 'Lab Internal (70 Marks)' },
  { code: 'PRACTICAL_EXAM', label: 'Practical Exam (50 Marks)' },
  { code: 'VIVA', label: 'Viva Voce (10 Marks)' },
];

interface MarksUploadStepProps {
  onAnalyzed: (batchId: string) => void;
}

export function MarksUploadStep({ onAnalyzed }: MarksUploadStepProps) {
  const [academicYearId, setAcademicYearId] = React.useState('');
  const [semesterId, setSemesterId] = React.useState('');
  const [departmentId, setDepartmentId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [subjectId, setSubjectId] = React.useState('');
  const [assessmentCode, setAssessmentCode] = React.useState('MID_WRITTEN');
  const [file, setFile] = React.useState<File | null>(null);

  const [isDragging, setIsDragging] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [touched, setTouched] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const { data: departments } = useQuery<Department[]>({
    queryKey: ['admin', 'departments'],
    queryFn: adminService.getDepartments,
  });

  const { data: sections } = useQuery<Section[]>({
    queryKey: ['admin', 'sections', departmentId],
    queryFn: () => adminService.getSections(departmentId),
    enabled: Boolean(departmentId),
  });

  const { data: subjects } = useQuery<Subject[]>({
    queryKey: ['admin', 'subjects', departmentId],
    queryFn: () => adminService.getSubjects(departmentId || undefined),
  });

  const { data: semesters } = useQuery<Semester[]>({
    queryKey: ['admin', 'semesters'],
    queryFn: () => adminService.getSemesters(),
  });

  const { data: academicYears } = useQuery<AcademicYear[]>({
    queryKey: ['admin', 'academic-years'],
    queryFn: () => adminService.getAcademicYears(),
  });

  const { data: templates } = useQuery<AssessmentTemplate[]>({
    queryKey: ['admin', 'assessment-templates', subjectId],
    queryFn: () => marksImportService.getTemplates(subjectId || undefined),
  });

  React.useEffect(() => {
    if (semesters && semesters.length > 0 && !semesterId) {
      setSemesterId((semesters.find((s) => s.is_current) ?? semesters[0]).id);
    }
  }, [semesters, semesterId]);

  const activeTemplate = templates?.find((t) => t.assessment_code === assessmentCode);

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type. Upload one of: ${ACCEPTED_EXTENSIONS.join(', ')}`;
    }
    if (f.size > 12 * 1024 * 1024) {
      return 'File is too large (max 12 MB).';
    }
    return null;
  };

  const handleFileSelect = (f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
  };

  const analyze = async () => {
    setTouched(true);
    if (!semesterId) {
      setError('Please select a Semester.');
      return;
    }
    if (!subjectId) {
      setError('Please select a Subject for the marks import.');
      return;
    }
    if (!file) {
      setError('Please upload a marks spreadsheet.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    try {
      const preview = await marksImportService.analyze(
        file,
        semesterId,
        subjectId,
        assessmentCode,
        academicYearId || undefined,
        departmentId || undefined,
        sectionId || undefined,
      );
      onAnalyzed(preview.batch_id);
    } catch (err: any) {
      setError(
        err?.response?.data?.error?.message ??
        err?.response?.data?.detail ??
        'Analysis failed. Check your spreadsheet format and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      {/* Parameters & Upload */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Award className="h-5 w-5 text-primary" />
                Assessment Parameters & Upload
              </CardTitle>
              <CardDescription>
                Select academic parameters, assessment type, and upload marks.
              </CardDescription>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => marksImportService.downloadDynamicTemplate(assessmentCode, subjectId || undefined)}
            >
              <Download className="mr-1.5 h-3.5 w-3.5 text-primary" />
              Download Template
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Academic Session */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">Academic Session</label>
              <select
                value={academicYearId}
                onChange={(e) => setAcademicYearId(e.target.value)}
                className={SELECT_CLASS}
              >
                <option value="">(Optional) Default Session</option>
                {academicYears?.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name} {ay.is_current ? '(Current)' : ''}
                  </option>
                ))}
              </select>
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
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Department */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">Department (Filter)</label>
              <select
                value={departmentId}
                onChange={(e) => {
                  setDepartmentId(e.target.value);
                  setSectionId('');
                }}
                className={SELECT_CLASS}
              >
                <option value="">All Departments</option>
                {departments?.map((d) => (
                  <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
                ))}
              </select>
            </div>

            {/* Section */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">Section (Filter)</label>
              <select
                value={sectionId}
                onChange={(e) => setSectionId(e.target.value)}
                className={SELECT_CLASS}
                disabled={!departmentId}
              >
                <option value="">All Sections</option>
                {sections?.map((sec) => (
                  <option key={sec.id} value={sec.id}>{sec.name} (Batch {sec.batch_year})</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Subject */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">
                Subject <span className="text-rose-500">*</span>
              </label>
              <select
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                className={SELECT_CLASS}
              >
                <option value="" disabled>Select subject…</option>
                {subjects?.map((subj) => (
                  <option key={subj.id} value={subj.id}>{subj.code} — {subj.name}</option>
                ))}
              </select>
              {touched && !subjectId && (
                <p className="text-[11px] font-medium text-rose-600">Subject is required.</p>
              )}
            </div>

            {/* Assessment Category */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">
                Assessment Category <span className="text-rose-500">*</span>
              </label>
              <select
                value={assessmentCode}
                onChange={(e) => setAssessmentCode(e.target.value)}
                className={SELECT_CLASS}
              >
                {ASSESSMENT_CATEGORIES.map((cat) => (
                  <option key={cat.code} value={cat.code}>{cat.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Drag & drop upload */}
          <div
            className={cn(
              'flex min-h-[150px] cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-6 transition-all duration-200',
              isDragging
                ? 'border-primary bg-primary/5'
                : file
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-border hover:border-primary/50 hover:bg-primary/5',
            )}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFileSelect(f);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED}
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileSelect(f);
              }}
            />
            {file ? (
              <div className="flex items-center gap-3 rounded-xl bg-emerald-500/10 px-4 py-3">
                <FileSpreadsheet className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <p className="text-sm font-bold text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <button
                  className="ml-4 rounded-full p-1 hover:bg-foreground/10"
                  onClick={(e) => { e.stopPropagation(); setFile(null); setError(null); }}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <>
                <UploadCloud className="h-8 w-8 text-muted-foreground" />
                <div className="text-center">
                  <p className="text-xs font-semibold text-foreground">Drop Excel marks sheet here or click to browse</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">.xlsx, .xls, .csv — max 12 MB</p>
                </div>
              </>
            )}
          </div>

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-700 dark:text-rose-300">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          <Button onClick={analyze} disabled={isAnalyzing} size="lg" className="w-full">
            {isAnalyzing ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Analyzing Marks File…
              </>
            ) : (
              'Analyze & Preview'
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Dynamic Template Format Info */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Dynamic Header Format</CardTitle>
          <CardDescription>
            {activeTemplate ? activeTemplate.assessment_name : 'Assessment Structure'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-border/50 bg-muted/30 p-3">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Generated Template Headers
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="px-2 py-1.5 text-left font-semibold">Student Roll Number</th>
                    {activeTemplate?.components && activeTemplate.components.length > 0 ? (
                      activeTemplate.components.map((c) => (
                        <th key={c.key} className="px-2 py-1.5 text-left font-semibold">
                          {c.key} ({c.max_marks}m)
                        </th>
                      ))
                    ) : (
                      <th className="px-2 py-1.5 text-left font-semibold">
                        Marks ({activeTemplate?.total_max_marks || 20}m)
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="text-muted-foreground">
                  <tr>
                    <td className="px-2 py-1 font-mono font-bold">23BQ1A5401</td>
                    {activeTemplate?.components && activeTemplate.components.length > 0 ? (
                      activeTemplate.components.map((c) => (
                        <td key={c.key} className="px-2 py-1">{round(c.max_marks * 0.9, 1)}</td>
                      ))
                    ) : (
                      <td className="px-2 py-1">{round((activeTemplate?.total_max_marks || 20) * 0.85, 1)}</td>
                    )}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-2 text-xs text-muted-foreground">
            <p className="font-bold text-foreground">Template Rules:</p>
            <ul className="list-disc pl-4 space-y-1">
              <li>Header column names must match question keys (e.g. <code>A</code>, <code>B</code>, <code>C</code>, <code>D</code>) or <code>Marks</code>.</li>
              <li>Scores must be numeric, non-negative, and not exceed the question/total maximum marks.</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function round(val: number, decimals: number) {
  return Math.round(val * Math.pow(10, decimals)) / Math.pow(10, decimals);
}
