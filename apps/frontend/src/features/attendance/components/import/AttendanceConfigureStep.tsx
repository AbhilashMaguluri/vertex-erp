import * as React from 'react';
import { ArrowLeft, Play, AlertCircle, ShieldCheck } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Modal } from '@/shared/components/ui/Modal';
import type {
  AttendanceImportConfiguration,
  AttendanceImportPreview,
} from '../../services/attendanceImport.service';

interface AttendanceConfigureStepProps {
  preview: AttendanceImportPreview;
  onBack: () => void;
  onStart: (config: AttendanceImportConfiguration) => void;
  isStarting: boolean;
  startError: string | null;
}

export function AttendanceConfigureStep({
  preview,
  onBack,
  onStart,
  isStarting,
  startError,
}: AttendanceConfigureStepProps) {
  const { summary } = preview;
  const [allowOverwrite, setAllowOverwrite] = React.useState(true);
  const [showConfirmModal, setShowConfirmModal] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowConfirmModal(true);
  };

  const confirmAndStart = () => {
    setShowConfirmModal(false);
    onStart({
      mode: summary.mode,
      attendance_date: summary.attendance_date,
      subject_id: preview.tables.records.length > 0 ? (preview.summary.subject_code || '') : '',
      allow_overwrite: allowOverwrite,
    });
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Review Attendance Import Settings</CardTitle>
            <CardDescription>
              Confirm the parameters and overwrite rules before writing records to the database.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                <span className="text-xs font-semibold text-muted-foreground">Import Mode</span>
                <p className="mt-1 font-bold text-foreground">{summary.mode === 'TODAY' ? "Today's Attendance" : 'Historical / Backdated'}</p>
              </div>

              <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                <span className="text-xs font-semibold text-muted-foreground">Attendance Date</span>
                <p className="mt-1 font-bold text-foreground">{summary.attendance_date}</p>
              </div>

              <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                <span className="text-xs font-semibold text-muted-foreground">Subject</span>
                <p className="mt-1 font-bold text-primary">{summary.subject_code} — {summary.subject_name || 'Subject'}</p>
              </div>
            </div>

            {/* Overwrite toggle */}
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowOverwrite}
                  onChange={(e) => setAllowOverwrite(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-input text-primary focus:ring-primary"
                />
                <div>
                  <span className="text-xs font-bold text-foreground">
                    Allow Overwriting Existing Attendance Records
                  </span>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    If checked, existing attendance records for the selected date and subject will be updated if the status in the file is different.
                  </p>
                </div>
              </label>
            </div>

            {startError && (
              <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs text-rose-700 dark:text-rose-300">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>{startError}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={onBack} disabled={isStarting}>
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Back to Preview
          </Button>
          <Button type="submit" size="lg" disabled={isStarting}>
            <Play className="mr-1.5 h-4 w-4 fill-current" /> Confirm & Import Attendance
          </Button>
        </div>
      </form>

      {/* Confirmation Modal */}
      <Modal
        open={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Confirm Attendance Import Execution"
        description="Please confirm execution. Records will be saved inside a database transaction."
        className="max-w-md"
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 flex items-start gap-2.5">
            <ShieldCheck className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 dark:text-amber-300">
              <p className="font-bold">Database Transaction Safety</p>
              <p className="mt-0.5">
                The import runs in a single transaction. If any failure occurs, no partial attendance records will be saved.
              </p>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <p className="font-bold uppercase tracking-wider text-muted-foreground">Import Summary</p>
            <div className="space-y-1.5">
              <div className="flex justify-between rounded-lg bg-muted/40 p-2">
                <span className="text-muted-foreground">Attendance Date:</span>
                <span className="font-bold text-foreground">{summary.attendance_date}</span>
              </div>
              <div className="flex justify-between rounded-lg bg-muted/40 p-2">
                <span className="text-muted-foreground">Records in File:</span>
                <span className="font-bold text-foreground">{summary.total_students_in_file}</span>
              </div>
              <div className="flex justify-between rounded-lg bg-muted/40 p-2">
                <span className="text-muted-foreground">New Records to Create:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">{summary.new_attendance_records}</span>
              </div>
              <div className="flex justify-between rounded-lg bg-muted/40 p-2">
                <span className="text-muted-foreground">Existing Records to Update:</span>
                <span className="font-bold text-amber-600 dark:text-amber-400">{summary.attendance_updates}</span>
              </div>
              {summary.missing_students > 0 && (
                <div className="flex justify-between rounded-lg bg-rose-500/10 p-2 text-rose-700 dark:text-rose-300">
                  <span className="font-bold">Missing Students (Skipped):</span>
                  <span className="font-bold">{summary.missing_students}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-border">
            <Button variant="outline" size="sm" onClick={() => setShowConfirmModal(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={confirmAndStart} disabled={isStarting}>
              {isStarting ? 'Importing…' : 'Import Attendance'}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
