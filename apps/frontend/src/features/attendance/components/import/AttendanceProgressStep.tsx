import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { attendanceImportService } from '../../services/attendanceImport.service';

interface AttendanceProgressStepProps {
  batchId: string;
  onDone: () => void;
  onFailed: (message: string) => void;
}

export function AttendanceProgressStep({ batchId, onDone, onFailed }: AttendanceProgressStepProps) {
  const { data: progress } = useQuery({
    queryKey: ['admin', 'attendance-imports', batchId, 'progress'],
    queryFn: () => attendanceImportService.getProgress(batchId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'COMPLETED' || status === 'FAILED' ? false : 1000;
    },
  });

  React.useEffect(() => {
    if (progress?.status === 'COMPLETED') onDone();
    if (progress?.status === 'FAILED') onFailed(progress.error || 'The attendance import failed. Nothing was saved.');
  }, [progress?.status, progress?.error, onDone, onFailed]);

  const percent = progress?.percent ?? 0;

  return (
    <Card className="mx-auto max-w-xl">
      <CardHeader className="text-center">
        <CardTitle className="text-base">Executing Attendance Import…</CardTitle>
        <CardDescription>
          Saving attendance records in a single database transaction.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="mb-2 flex items-center justify-between text-xs font-bold">
            <span className="text-foreground">{progress?.message ?? 'Saving attendance…'}</span>
            <span className="font-mono text-primary">{percent}%</span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-muted/60">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary to-primary/80 transition-all duration-500 ease-out"
              style={{ width: `${percent}%` }}
            />
          </div>
          {progress && progress.total > 0 && (
            <p className="mt-1.5 text-right text-[11px] font-medium text-muted-foreground">
              {progress.processed} / {progress.total}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
