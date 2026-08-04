import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  X,
  Calendar,
  Clock,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { adminService, Subject, Department, Section } from '@/features/admin/services/admin.service';
import { cn } from '@/shared/utils/cn';
import { attendanceImportService } from '../../services/attendanceImport.service';

const ACCEPTED = '.xlsx,.xlsm,.xls,.csv';
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm', '.xls', '.csv'];

const SELECT_CLASS =
  'h-10 w-full rounded-xl border border-input bg-background/60 px-3 text-xs font-semibold shadow-xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring';

interface AttendanceUploadStepProps {
  onAnalyzed: (batchId: string) => void;
}

export function AttendanceUploadStep({ onAnalyzed }: AttendanceUploadStepProps) {
  const [mode, setMode] = React.useState<'TODAY' | 'PAST'>('TODAY');
  const [attendanceDate, setAttendanceDate] = React.useState(new Date().toISOString().split('T')[0]);
  const [departmentId, setDepartmentId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [subjectId, setSubjectId] = React.useState('');
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
    if (!subjectId) {
      setError('Please select a Subject for the attendance records.');
      return;
    }
    if (!file) {
      setError('Please upload an attendance Excel file.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    try {
      const preview = await attendanceImportService.analyze(
        file,
        mode,
        mode === 'PAST' ? attendanceDate : undefined,
        subjectId,
        departmentId || undefined,
        sectionId || undefined,
      );
      onAnalyzed(preview.batch_id);
    } catch (err: any) {
      setError(
        err?.response?.data?.error?.message ??
        err?.response?.data?.detail ??
        'Analysis failed. Check your file format and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Option Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div
          onClick={() => setMode('TODAY')}
          className={cn(
            'cursor-pointer rounded-2xl border-2 p-5 transition-all duration-200',
            mode === 'TODAY'
              ? 'border-primary bg-primary/5 shadow-md'
              : 'border-border hover:border-primary/40 hover:bg-muted/30'
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-xl', mode === 'TODAY' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <p className="font-bold text-foreground">Option 1 — Today's Attendance</p>
              <p className="text-xs text-muted-foreground">Uses today's date automatically ({new Date().toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })})</p>
            </div>
          </div>
        </div>

        <div
          onClick={() => setMode('PAST')}
          className={cn(
            'cursor-pointer rounded-2xl border-2 p-5 transition-all duration-200',
            mode === 'PAST'
              ? 'border-primary bg-primary/5 shadow-md'
              : 'border-border hover:border-primary/40 hover:bg-muted/30'
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-xl', mode === 'PAST' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <p className="font-bold text-foreground">Option 2 — Upload Past Attendance</p>
              <p className="text-xs text-muted-foreground">Select a custom date for historical or backdated imports</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Parameters & File Upload */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <UploadCloud className="h-5 w-5 text-primary" />
              Import Parameters & File
            </CardTitle>
            <CardDescription>
              Select the subject and upload your two-column attendance spreadsheet.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Date picker for PAST mode */}
            {mode === 'PAST' && (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">
                  Attendance Date <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="date"
                  value={attendanceDate}
                  onChange={(e) => setAttendanceDate(e.target.value)}
                  className="h-10"
                />
              </div>
            )}

            {/* Department (optional filter) */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">Department (Optional Filter)</label>
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

              {/* Section (optional filter) */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground">Section (Optional Filter)</label>
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

            {/* Subject selection (REQUIRED) */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground">
                Subject / Course <span className="text-rose-500">*</span>
              </label>
              <select
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                className={SELECT_CLASS}
              >
                <option value="" disabled>Select Subject…</option>
                {subjects?.map((subj) => (
                  <option key={subj.id} value={subj.id}>
                    {subj.code} — {subj.name}
                  </option>
                ))}
              </select>
              {touched && !subjectId && (
                <p className="text-[11px] font-medium text-rose-600">Subject is required for attendance records.</p>
              )}
            </div>

            {/* Drag & drop upload */}
            <div
              className={cn(
                'flex min-h-[160px] cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-6 transition-all duration-200',
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
                    <p className="text-xs font-semibold text-foreground">Drop Excel file here or click to browse</p>
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
                  Analyzing Attendance File…
                </>
              ) : (
                'Analyze & Preview'
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Expected Format & Rules */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Expected Template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-border/50 bg-muted/30 p-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Two Column Format
              </p>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="px-2 py-1.5 text-left font-semibold">Student Roll Number</th>
                    <th className="px-2 py-1.5 text-left font-semibold">Attendance Status</th>
                  </tr>
                </thead>
                <tbody className="text-muted-foreground">
                  <tr><td className="px-2 py-1 font-mono font-bold">23BQ1A5401</td><td className="px-2 py-1">Present</td></tr>
                  <tr><td className="px-2 py-1 font-mono font-bold">23BQ1A5402</td><td className="px-2 py-1">Absent</td></tr>
                  <tr><td className="px-2 py-1 font-mono font-bold">23BQ1A5403</td><td className="px-2 py-1">P</td></tr>
                  <tr><td className="px-2 py-1 font-mono font-bold">23BQ1A5404</td><td className="px-2 py-1">A</td></tr>
                  <tr><td className="px-2 py-1 font-mono font-bold">23BQ1A5405</td><td className="px-2 py-1">OD</td></tr>
                </tbody>
              </table>
            </div>

            <div className="space-y-2 text-xs text-muted-foreground">
              <p className="font-bold text-foreground">Accepted Status Values:</p>
              <ul className="list-disc pl-4 space-y-1">
                <li><strong className="text-foreground">Present</strong> / P / 1 / YES → Present</li>
                <li><strong className="text-foreground">Absent</strong> / A / 0 / NO → Absent</li>
                <li><strong className="text-foreground">On Duty</strong> / OD → On Duty</li>
                <li><strong className="text-foreground">Medical Leave</strong> / ML → Medical Leave</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
