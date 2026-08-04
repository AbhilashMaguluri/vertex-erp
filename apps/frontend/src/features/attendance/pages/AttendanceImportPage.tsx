import * as React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  UploadCloud,
  ListChecks,
  SlidersHorizontal,
  PlayCircle,
  CheckCircle2,
  History,
  TrendingUp,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  CalendarCheck,
} from 'lucide-react';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { ImportStepper, ImportStep, StepDefinition } from '@/features/admin/components/import/ImportStepper';
import { AttendanceUploadStep } from '../components/import/AttendanceUploadStep';
import { AttendancePreviewStep } from '../components/import/AttendancePreviewStep';
import { AttendanceConfigureStep } from '../components/import/AttendanceConfigureStep';
import { AttendanceProgressStep } from '../components/import/AttendanceProgressStep';
import { AttendanceCompleteStep } from '../components/import/AttendanceCompleteStep';
import {
  attendanceImportService,
  AttendanceImportConfiguration,
} from '../services/attendanceImport.service';

const STEPS: StepDefinition[] = [
  { id: 1, label: 'Upload', hint: 'Select mode & upload Excel file', icon: UploadCloud },
  { id: 2, label: 'Preview', hint: 'Review match & resolution status', icon: ListChecks },
  { id: 3, label: 'Configure', hint: 'Set overwrite & review settings', icon: SlidersHorizontal },
  { id: 4, label: 'Import', hint: 'Executing in transaction', icon: PlayCircle },
  { id: 5, label: 'Completed', hint: 'Summary & downloadable report', icon: CheckCircle2 },
];

const STATUS_BADGE: Record<string, 'success' | 'info' | 'warning' | 'destructive' | 'secondary'> = {
  COMPLETED: 'success',
  RUNNING: 'info',
  ANALYZED: 'warning',
  FAILED: 'destructive',
};

export function AttendanceImportPage() {
  const queryClient = useQueryClient();

  const [step, setStep] = React.useState<ImportStep>(1);
  const [batchId, setBatchId] = React.useState<string | null>(null);
  const [isStarting, setIsStarting] = React.useState(false);
  const [startError, setStartError] = React.useState<string | null>(null);
  const [runError, setRunError] = React.useState<string | null>(null);

  const { data: preview, isLoading: loadingPreview } = useQuery({
    queryKey: ['admin', 'attendance-imports', batchId, 'preview'],
    queryFn: () => attendanceImportService.getPreview(batchId as string),
    enabled: Boolean(batchId) && step >= 2 && step <= 3,
  });

  const { data: history, isLoading: loadingHistory } = useQuery({
    queryKey: ['admin', 'attendance-imports', 'history'],
    queryFn: () => attendanceImportService.getHistory(15),
  });

  const reset = () => {
    setBatchId(null);
    setStep(1);
    setStartError(null);
    setRunError(null);
    queryClient.invalidateQueries({ queryKey: ['admin', 'attendance-imports', 'history'] });
  };

  const handleStart = async (config: AttendanceImportConfiguration) => {
    if (!batchId) return;
    setIsStarting(true);
    setStartError(null);
    try {
      await attendanceImportService.execute(batchId, config);
      setStep(4);
    } catch (err: any) {
      setStartError(err?.response?.data?.error?.message ?? 'The attendance import could not be started.');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Attendance', href: '/attendance' },
          { label: 'Attendance Import' },
        ]}
      />
      <PageHeader
        title="Enterprise Attendance Import"
        subtitle="Bulk import daily or backdated attendance records for courses and sections using simple two-column spreadsheets."
        actions={
          step === 1 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => attendanceImportService.downloadSampleTemplate()}
            >
              <FileSpreadsheet className="mr-1.5 h-4 w-4" />
              Sample Template
            </Button>
          ) : undefined
        }
      />

      <div className="my-6">
        <ImportStepper
          steps={STEPS}
          current={step}
          navigableUpTo={step >= 4 ? 0 : 3}
          onNavigate={(target) => {
            setStartError(null);
            setStep(target);
          }}
        />
      </div>

      {runError && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <div className="min-w-0 flex-1 text-xs leading-relaxed text-rose-700 dark:text-rose-300">
            <p className="font-bold">The attendance import failed and was completely rolled back.</p>
            <p className="mt-0.5 font-medium">{runError}</p>
          </div>
          <Button variant="outline" size="sm" onClick={reset}>
            Start Over
          </Button>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-6">
          <AttendanceUploadStep
            onAnalyzed={(id) => {
              setBatchId(id);
              setStep(2);
              queryClient.invalidateQueries({ queryKey: ['admin', 'attendance-imports', 'history'] });
            }}
          />
          <AttendanceDashboard history={history} isLoading={loadingHistory} />
        </div>
      )}

      {step === 2 &&
        (loadingPreview || !preview ? (
          <Skeleton className="h-96 w-full rounded-2xl" />
        ) : (
          <AttendancePreviewStep
            preview={preview}
            onBack={reset}
            onContinue={() => setStep(3)}
          />
        ))}

      {step === 3 &&
        (loadingPreview || !preview ? (
          <Skeleton className="h-96 w-full rounded-2xl" />
        ) : (
          <AttendanceConfigureStep
            preview={preview}
            onBack={() => setStep(2)}
            onStart={handleStart}
            isStarting={isStarting}
            startError={startError}
          />
        ))}

      {step === 4 && batchId && (
        <AttendanceProgressStep
          batchId={batchId}
          onDone={() => {
            setStep(5);
            queryClient.invalidateQueries({ queryKey: ['admin', 'attendance-imports', 'history'] });
            queryClient.invalidateQueries({ queryKey: ['attendance'] });
            queryClient.invalidateQueries({ queryKey: ['reports'] });
          }}
          onFailed={(message) => {
            setRunError(message);
            setStep(3);
          }}
        />
      )}

      {step === 5 && batchId && (
        <AttendanceCompleteStep batchId={batchId} onStartAnother={reset} />
      )}
    </>
  );
}

function AttendanceDashboard({
  history,
  isLoading,
}: {
  history?: Awaited<ReturnType<typeof attendanceImportService.getHistory>>;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <Skeleton className="h-64 w-full rounded-2xl" />;
  }

  const lastImport = history?.last_import_at ? new Date(history.last_import_at) : null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Imports Run"
          value={history?.total_imports ?? 0}
          icon={History}
          description={`${history?.completed_imports ?? 0} completed successfully`}
        />
        <StatCard
          title="Success Rate"
          value={`${history?.success_rate ?? 0}%`}
          icon={TrendingUp}
          progress={history?.success_rate ?? 0}
          description="Completed imports as a share of all uploads"
        />
        <StatCard
          title="Attendance Records Saved"
          value={(history?.total_records_created ?? 0) + (history?.total_records_updated ?? 0)}
          icon={CalendarCheck}
          description={`${history?.total_records_created ?? 0} created, ${history?.total_records_updated ?? 0} updated`}
        />
        <StatCard
          title="Last Import"
          value={lastImport ? lastImport.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : '—'}
          icon={Clock}
          description={lastImport ? lastImport.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : 'No imports yet'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="h-4 w-4 text-primary" />
            Attendance Import History
          </CardTitle>
          <CardDescription>
            History of attendance spreadsheet uploads, modes, and outcomes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!history || history.items.length === 0 ? (
            <EmptyState
              icon={UploadCloud}
              title="No attendance imports yet"
              description="Upload your first attendance Excel sheet above to record bulk attendance."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Attendance Date</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Imported By</TableHead>
                  <TableHead className="text-right">Created</TableHead>
                  <TableHead className="text-right">Updated</TableHead>
                  <TableHead className="text-right">Failed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.items.map((item) => (
                  <TableRow key={item.batch_id}>
                    <TableCell>
                      <div className="flex items-center gap-2.5">
                        <FileSpreadsheet className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="font-semibold text-foreground">{item.file_name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{item.mode}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs font-bold">{item.attendance_date}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{item.subject_name || '—'}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[item.status] ?? 'secondary'} dot>
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.imported_by ?? '—'}</TableCell>
                    <TableCell className="text-right font-bold text-emerald-600 dark:text-emerald-400">{item.records_created}</TableCell>
                    <TableCell className="text-right text-amber-600 dark:text-amber-400 font-semibold">{item.records_updated}</TableCell>
                    <TableCell className="text-right">
                      {item.failed_records > 0 ? (
                        <span className="font-bold text-rose-600 dark:text-rose-400">{item.failed_records}</span>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
