import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, FileSpreadsheet, RotateCcw } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { marksImportService } from '../../services/marksImport.service';

interface MarksCompleteStepProps {
  batchId: string;
  onStartAnother: () => void;
}

export function MarksCompleteStep({ batchId, onStartAnother }: MarksCompleteStepProps) {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['admin', 'marks-imports', batchId, 'summary'],
    queryFn: () => marksImportService.getSummary(batchId),
  });

  if (isLoading || !summary) {
    return <Skeleton className="h-96 w-full rounded-2xl" />;
  }

  return (
    <div className="space-y-6">
      {/* Banner */}
      <Card className="border-emerald-500/30 bg-emerald-500/5">
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Marks Import Completed!</h2>
              <p className="text-xs text-muted-foreground">
                Subject: {summary.subject_code} ({summary.assessment_code}) | {summary.records_created} created, {summary.records_updated} updated.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => marksImportService.downloadReport(batchId)}>
              <FileSpreadsheet className="mr-1.5 h-4 w-4" /> Download Report
            </Button>
            <Button size="sm" onClick={onStartAnother}>
              <RotateCcw className="mr-1.5 h-4 w-4" /> Start Another
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Created</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{summary.records_created}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Updated</p>
          <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">{summary.records_updated}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Skipped</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{summary.records_skipped}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Failed</p>
          <p className="mt-1 text-2xl font-bold text-rose-600 dark:text-rose-400">{summary.failed_records}</p>
        </div>
      </div>

      {/* Audit Log Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Processed Record Outcomes</CardTitle>
          <CardDescription>Outcome for each student roll number in the uploaded spreadsheet.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-[380px] overflow-auto rounded-lg border border-border/30">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Roll Number</TableHead>
                  <TableHead>Student Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Message</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.records.map((r, idx) => (
                  <TableRow key={`${r.identifier}-${idx}`}>
                    <TableCell className="font-mono text-xs font-bold">{r.identifier}</TableCell>
                    <TableCell className="text-xs">{r.display_name || '—'}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          r.status === 'CREATED' ? 'success' :
                          r.status === 'UPDATED' ? 'warning' :
                          r.status === 'SKIPPED' ? 'secondary' : 'destructive'
                        }
                      >
                        {r.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{r.message || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
