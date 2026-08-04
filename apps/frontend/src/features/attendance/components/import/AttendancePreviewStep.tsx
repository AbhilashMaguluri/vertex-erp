import * as React from 'react';
import {
  Users,
  Calendar,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  Download,
  Search,
  BookOpen,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardHeader } from '@/shared/components/ui/Card';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { Input } from '@/shared/components/ui/Input';
import type { AttendanceImportPreview } from '../../services/attendanceImport.service';
import { attendanceImportService } from '../../services/attendanceImport.service';

interface AttendancePreviewStepProps {
  preview: AttendanceImportPreview;
  onBack: () => void;
  onContinue: () => void;
}

export function AttendancePreviewStep({ preview, onBack, onContinue }: AttendancePreviewStepProps) {
  const [searchTerm, setSearchTerm] = React.useState('');
  const { summary, tables, validation_errors } = preview;

  const hasErrors = summary.errors > 0 || summary.missing_students > 0;
  const hasWarnings = summary.warnings > 0;

  const filtered = tables.records.filter((r) =>
    !searchTerm ||
    r.roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.student_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 xl:grid-cols-8">
        <StatCard
          title="Date"
          value={summary.attendance_date}
          icon={Calendar}
          description={summary.mode === 'TODAY' ? "Today's Attendance" : 'Historical Date'}
        />
        <StatCard
          title="Course"
          value={summary.subject_code || '—'}
          icon={BookOpen}
          description={summary.subject_name || 'Subject'}
        />
        <StatCard
          title="Students in File"
          value={summary.total_students_in_file}
          icon={Users}
          description={`${summary.existing_students_found} found in DB`}
        />
        <StatCard
          title="Missing Students"
          value={summary.missing_students}
          icon={AlertCircle}
          description="Cannot be imported"
        />
        <StatCard
          title="New Records"
          value={summary.new_attendance_records}
          icon={CheckCircle2}
          description="Will be created"
        />
        <StatCard
          title="Updates"
          value={summary.attendance_updates}
          icon={RefreshCw}
          description="Existing records"
        />
        <StatCard
          title="Skipped"
          value={summary.skipped_records}
          icon={Users}
          description="No status change"
        />
        <StatCard
          title="Errors"
          value={summary.errors}
          icon={AlertCircle}
          description={`${summary.warnings} warnings`}
        />
      </div>

      {/* Alerts */}
      {hasErrors && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
          <div className="flex-1">
            <p className="text-sm font-bold text-rose-700 dark:text-rose-300">
              {summary.errors} error(s) found in attendance file
            </p>
            <p className="mt-0.5 text-xs text-rose-600/80 dark:text-rose-400/80">
              {summary.missing_students > 0 &&
                `${summary.missing_students} student(s) could not be found in the institution database. `}
              Rows with errors will be skipped during execution.
              {validation_errors.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-2 h-6 text-xs"
                  onClick={() => attendanceImportService.downloadErrorReport(preview.batch_id)}
                >
                  <Download className="mr-1 h-3 w-3" /> Download Attendance_Import_Errors.xlsx
                </Button>
              )}
            </p>
          </div>
        </div>
      )}

      {hasWarnings && !hasErrors && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{summary.warnings} warning(s) — review before continuing.</p>
        </div>
      )}

      {/* Preview Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-base font-bold text-foreground">Attendance Records Detailed Preview</h3>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search roll number or status…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-8 pl-8 text-xs"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="max-h-[420px] overflow-auto rounded-lg border border-border/30">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Roll Number</TableHead>
                  <TableHead>Student Name</TableHead>
                  <TableHead>Status in File</TableHead>
                  <TableHead>Student Found</TableHead>
                  <TableHead>Existing Attendance</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                      No matching records found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.slice(0, 250).map((r, i) => (
                    <TableRow key={`${r.roll_number}-${i}`}>
                      <TableCell className="font-mono text-xs font-bold">{r.roll_number}</TableCell>
                      <TableCell className="text-xs">{r.student_name || '—'}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            r.status === 'Present' ? 'success' :
                            r.status === 'Absent' ? 'destructive' :
                            'info'
                          }
                        >
                          {r.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={r.student_found === 'Yes' ? 'success' : 'destructive'} dot>
                          {r.student_found}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{r.existing_attendance}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            r.action === 'Create' ? 'success' :
                            r.action === 'Update' ? 'warning' :
                            r.action === 'Cannot Import' ? 'destructive' :
                            'secondary'
                          }
                        >
                          {r.action}
                        </Badge>
                        {r.error && (
                          <p className="mt-0.5 text-[10px] text-rose-600 dark:text-rose-400">{r.error}</p>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            {filtered.length > 250 && (
              <p className="py-2 text-center text-xs text-muted-foreground">
                Showing first 250 of {filtered.length} records
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Nav */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-1.5 h-4 w-4" /> Back
        </Button>
        <Button onClick={onContinue}>
          Configure & Import <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
