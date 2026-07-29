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
  GraduationCap,
  Clock,
  AlertCircle,
  FileSpreadsheet,
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
import { ImportStepper, ImportStep, StepDefinition } from '../components/import/ImportStepper';
import { UploadStep } from '../components/import/UploadStep';
import { PreviewStep } from '../components/import/PreviewStep';
import { ConfigureStep } from '../components/import/ConfigureStep';
import { ImportProgressStep } from '../components/import/ImportProgressStep';
import { CompleteStep } from '../components/import/CompleteStep';
import { officeImportService, ImportConfiguration } from '../services/import.service';

const STEPS: StepDefinition[] = [
  { id: 1, label: 'Upload', hint: 'Upload the office Excel or CSV file', icon: UploadCloud },
  { id: 2, label: 'Preview', hint: 'Check what the importer understood', icon: ListChecks },
  { id: 3, label: 'Configure', hint: 'Fill in whatever the file did not say', icon: SlidersHorizontal },
  { id: 4, label: 'Import', hint: 'Provisioning accounts', icon: PlayCircle },
  { id: 5, label: 'Completed', hint: 'Summary, credentials and report', icon: CheckCircle2 },
];

const STATUS_BADGE: Record<string, 'success' | 'info' | 'warning' | 'destructive' | 'secondary'> = {
  COMPLETED: 'success',
  RUNNING: 'info',
  ANALYZED: 'warning',
  FAILED: 'destructive',
};

export function OfficeImportPage() {
  const queryClient = useQueryClient();

  const [step, setStep] = React.useState<ImportStep>(1);
  const [batchId, setBatchId] = React.useState<string | null>(null);
  const [isStarting, setIsStarting] = React.useState(false);
  const [startError, setStartError] = React.useState<string | null>(null);
  const [runError, setRunError] = React.useState<string | null>(null);

  const { data: preview, isLoading: loadingPreview } = useQuery({
    queryKey: ['admin', 'imports', batchId, 'preview'],
    queryFn: () => officeImportService.getPreview(batchId as string),
    enabled: Boolean(batchId) && step >= 2 && step <= 3,
  });

  const { data: history, isLoading: loadingHistory } = useQuery({
    queryKey: ['admin', 'imports', 'history'],
    queryFn: () => officeImportService.getHistory(15),
  });

  const reset = () => {
    setBatchId(null);
    setStep(1);
    setStartError(null);
    setRunError(null);
    queryClient.invalidateQueries({ queryKey: ['admin', 'imports', 'history'] });
  };

  const handleStart = async (config: ImportConfiguration) => {
    if (!batchId) return;
    setIsStarting(true);
    setStartError(null);
    try {
      await officeImportService.execute(batchId, config);
      setStep(4);
    } catch (err: any) {
      setStartError(err?.response?.data?.error?.message ?? 'The import could not be started.');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Administration' },
          { label: 'User Directory', href: '/admin/users' },
          { label: 'Office Import' },
        ]}
      />
      <PageHeader
        title="Office Import"
        subtitle="Upload the allotment sheet your college office already keeps — roll ranges, counsellors, accounts and assignments are all worked out from it"
        actions={
          step === 1 ? (
            <Button variant="outline" size="sm" onClick={() => officeImportService.downloadSampleTemplate()}>
              <FileSpreadsheet className="mr-1.5 h-4 w-4" />
              Sample template
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
            <p className="font-bold">The import failed and was rolled back.</p>
            <p className="mt-0.5 font-medium">{runError}</p>
          </div>
          <Button variant="outline" size="sm" onClick={reset}>
            Start over
          </Button>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-6">
          <UploadStep
            onAnalyzed={(id) => {
              setBatchId(id);
              setStep(2);
              queryClient.invalidateQueries({ queryKey: ['admin', 'imports', 'history'] });
            }}
          />
          <ImportDashboard history={history} isLoading={loadingHistory} />
        </div>
      )}

      {step === 2 &&
        (loadingPreview || !preview ? (
          <Skeleton className="h-96 w-full rounded-2xl" />
        ) : (
          <PreviewStep preview={preview} onBack={reset} onContinue={() => setStep(3)} />
        ))}

      {step === 3 &&
        (loadingPreview || !preview ? (
          <Skeleton className="h-96 w-full rounded-2xl" />
        ) : (
          <ConfigureStep
            preview={preview}
            onBack={() => setStep(2)}
            onStart={handleStart}
            isStarting={isStarting}
            startError={startError}
          />
        ))}

      {step === 4 && batchId && (
        <ImportProgressStep
          batchId={batchId}
          onDone={() => {
            setStep(5);
            queryClient.invalidateQueries({ queryKey: ['admin', 'imports', 'history'] });
            queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
          }}
          onFailed={(message) => {
            setRunError(message);
            setStep(3);
          }}
        />
      )}

      {step === 5 && batchId && <CompleteStep batchId={batchId} onStartAnother={reset} />}
    </>
  );
}

function ImportDashboard({
  history,
  isLoading,
}: {
  history?: Awaited<ReturnType<typeof officeImportService.getHistory>>;
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
          title="Imports run"
          value={history?.total_imports ?? 0}
          icon={History}
          description={`${history?.completed_imports ?? 0} completed successfully`}
        />
        <StatCard
          title="Success rate"
          value={`${history?.success_rate ?? 0}%`}
          icon={TrendingUp}
          progress={history?.success_rate ?? 0}
          description="Completed imports as a share of all uploads"
        />
        <StatCard
          title="Students provisioned"
          value={history?.total_students_created ?? 0}
          icon={GraduationCap}
          description={`${history?.total_counsellors_created ?? 0} counsellors created alongside them`}
        />
        <StatCard
          title="Last import"
          value={lastImport ? lastImport.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : '—'}
          icon={Clock}
          description={lastImport ? lastImport.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : 'No imports yet'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-4 w-4 text-primary" />
            Import history
          </CardTitle>
          <CardDescription>Every office file uploaded, and what it produced.</CardDescription>
        </CardHeader>
        <CardContent>
          {!history || history.items.length === 0 ? (
            <EmptyState
              icon={UploadCloud}
              title="No imports yet"
              description="Upload your first office allotment sheet above. The importer will show you exactly what it plans to create before anything is written."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Imported by</TableHead>
                  <TableHead>When</TableHead>
                  <TableHead className="text-right">Students</TableHead>
                  <TableHead className="text-right">Counsellors</TableHead>
                  <TableHead className="text-right">Skipped</TableHead>
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
                      <Badge variant={STATUS_BADGE[item.status] ?? 'secondary'} dot>
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.imported_by ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(item.created_at).toLocaleString(undefined, {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </TableCell>
                    <TableCell className="text-right font-bold text-foreground">{item.students_created}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{item.counsellors_created}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{item.students_skipped}</TableCell>
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
