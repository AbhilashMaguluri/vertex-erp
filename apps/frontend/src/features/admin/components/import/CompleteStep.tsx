import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Download,
  FileSpreadsheet,
  FileText,
  KeyRound,
  RotateCcw,
  ShieldAlert,
  Trash2,
  Users,
  XCircle,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { cn } from '@/shared/utils/cn';
import { officeImportService, ImportSummary } from '../../services/import.service';

interface CompleteStepProps {
  batchId: string;
  onStartAnother: () => void;
}

export function CompleteStep({ batchId, onStartAnother }: CompleteStepProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showPasswords, setShowPasswords] = React.useState(false);
  const [tab, setTab] = React.useState<'credentials' | 'records'>('credentials');

  const { data: summary, isLoading } = useQuery({
    queryKey: ['admin', 'imports', batchId, 'summary'],
    queryFn: () => officeImportService.getSummary(batchId),
  });

  const { data: credentials } = useQuery({
    queryKey: ['admin', 'imports', batchId, 'credentials'],
    queryFn: () => officeImportService.getCredentials(batchId, 100),
    enabled: Boolean(summary?.credentials_available),
    retry: false,
  });

  const purge = useMutation({
    mutationFn: () => officeImportService.purgeCredentials(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'imports'] });
    },
  });

  if (isLoading || !summary) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  const outcomes = [
    { label: 'Students created', value: summary.students_created, icon: CheckCircle2, tone: 'success' as const },
    { label: 'Counsellors created', value: summary.counsellors_created, icon: Users, tone: 'success' as const },
    { label: 'Existing counsellors reused', value: summary.counsellors_reused, icon: Users, tone: 'info' as const },
    { label: 'Duplicate students skipped', value: summary.students_skipped, icon: RotateCcw, tone: 'warning' as const },
    { label: 'Counsellor assignments', value: summary.assignments_created, icon: KeyRound, tone: 'info' as const },
    { label: 'Failed records', value: summary.failed_records, icon: XCircle, tone: 'destructive' as const },
  ];

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-emerald-500/30">
        <div className="flex flex-col items-center gap-4 bg-gradient-to-br from-emerald-500/10 to-transparent p-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-600 ring-8 ring-emerald-500/5">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-lg font-black tracking-tight text-foreground">Import complete</h2>
            <p className="mt-1 text-xs font-medium text-muted-foreground">
              <span className="font-mono text-foreground">{summary.file_name}</span> ·{' '}
              {summary.students_created} student{summary.students_created === 1 ? '' : 's'} and{' '}
              {summary.counsellors_created} counsellor{summary.counsellors_created === 1 ? '' : 's'} are now in the
              User Directory.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-2">
            <Button size="sm" onClick={() => navigate('/admin/users')}>
              <Users className="mr-1.5 h-4 w-4" />
              Open User Directory
            </Button>
            <Button variant="outline" size="sm" onClick={onStartAnother}>
              <RotateCcw className="mr-1.5 h-4 w-4" />
              Import another file
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        {outcomes.map(({ label, value, icon: Icon, tone }) => (
          <div
            key={label}
            className={cn(
              'flex items-center gap-3 rounded-2xl border bg-card p-4 shadow-xs',
              tone === 'destructive' && value > 0 ? 'border-rose-500/30' : 'border-border/70'
            )}
          >
            <div
              className={cn(
                'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
                tone === 'success' && 'bg-emerald-500/10 text-emerald-600',
                tone === 'info' && 'bg-sky-500/10 text-sky-600',
                tone === 'warning' && 'bg-amber-500/10 text-amber-600',
                tone === 'destructive' && 'bg-rose-500/10 text-rose-600'
              )}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-black leading-none tracking-tight text-foreground">{value}</p>
              <p className="mt-1 text-[11px] font-bold leading-tight text-muted-foreground">{label}</p>
            </div>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-4 w-4 text-primary" />
            Download
          </CardTitle>
          <CardDescription>
            The credentials workbook holds one sheet of students and one of counsellors. The report accounts for
            every row of the source file.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button
            onClick={() => officeImportService.downloadCredentials(batchId)}
            disabled={!summary.credentials_available}
          >
            <KeyRound className="mr-1.5 h-4 w-4" />
            Credentials (Excel)
          </Button>
          <Button variant="outline" onClick={() => officeImportService.downloadReportExcel(batchId)}>
            <FileSpreadsheet className="mr-1.5 h-4 w-4" />
            Import report (Excel)
          </Button>
          <Button variant="outline" onClick={() => officeImportService.downloadReportPdf(batchId)}>
            <FileText className="mr-1.5 h-4 w-4" />
            Import report (PDF)
          </Button>
        </CardContent>
      </Card>

      {summary.credentials_available && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="min-w-0 flex-1 text-xs leading-relaxed text-amber-800 dark:text-amber-200">
            <p className="font-bold">These temporary passwords are readable until you purge them.</p>
            <p className="mt-0.5 font-medium">
              They have to be, so you can hand them out — a hash cannot be printed on a slip. Every account must
              change its password at first login. Download the workbook, distribute it privately, then purge.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="shrink-0 border-amber-500/40 text-amber-800 hover:bg-amber-500/20 dark:text-amber-200"
            onClick={() => purge.mutate()}
            isLoading={purge.isPending}
          >
            <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            Purge stored passwords
          </Button>
        </div>
      )}

      <div>
        <div className="mb-4 flex gap-1 border-b border-border/80 pb-2 select-none">
          {([
            { key: 'credentials' as const, label: 'Generated credentials', count: summary.credential_count },
            { key: 'records' as const, label: 'Record outcomes', count: summary.records.length },
          ]).map((entry) => (
            <button
              key={entry.key}
              onClick={() => setTab(entry.key)}
              className={cn(
                'flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer',
                tab === entry.key
                  ? 'bg-brand-600 text-white font-black shadow-md shadow-brand-600/25'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              )}
            >
              {entry.label}
              <span
                className={cn(
                  'rounded-full px-1.5 py-0.5 text-[10px] font-black',
                  tab === entry.key ? 'bg-white/20' : 'bg-muted'
                )}
              >
                {entry.count}
              </span>
            </button>
          ))}
        </div>

        {tab === 'credentials' ? (
          <CredentialsPanel
            summary={summary}
            credentials={credentials}
            showPasswords={showPasswords}
            onToggle={() => setShowPasswords((value) => !value)}
          />
        ) : (
          <RecordsPanel summary={summary} />
        )}
      </div>
    </div>
  );
}

function CredentialsPanel({
  summary,
  credentials,
  showPasswords,
  onToggle,
}: {
  summary: ImportSummary;
  credentials?: Awaited<ReturnType<typeof officeImportService.getCredentials>>;
  showPasswords: boolean;
  onToggle: () => void;
}) {
  if (!summary.credentials_available) {
    return (
      <div className="rounded-xl border border-dashed border-border/80 bg-card/50 p-10 text-center shadow-xs">
        <p className="text-xs font-medium text-muted-foreground">
          The stored passwords for this import have been purged. Reset an individual account from the User
          Directory if someone still needs theirs.
        </p>
      </div>
    );
  }

  if (!credentials) {
    return <Skeleton className="h-48 w-full rounded-xl" />;
  }

  return (
    <>
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[11px] font-medium text-muted-foreground">
          Showing {credentials.length} of {summary.credential_count}. Download the workbook for the complete list.
        </p>
        <Button variant="ghost" size="sm" onClick={onToggle}>
          {showPasswords ? <EyeOff className="mr-1.5 h-3.5 w-3.5" /> : <Eye className="mr-1.5 h-3.5 w-3.5" />}
          {showPasswords ? 'Hide passwords' : 'Reveal passwords'}
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Identifier</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Username</TableHead>
            <TableHead>Temporary password</TableHead>
            <TableHead>Counsellor</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {credentials.map((credential) => (
            <TableRow key={`${credential.record_type}-${credential.username}`}>
              <TableCell className="font-mono font-bold text-foreground">{credential.identifier}</TableCell>
              <TableCell>{credential.full_name}</TableCell>
              <TableCell className="font-mono text-muted-foreground">{credential.username}</TableCell>
              <TableCell>
                <span className="rounded-md bg-muted px-2 py-1 font-mono text-[11px] font-bold text-foreground">
                  {showPasswords ? credential.temporary_password : '••••••••'}
                </span>
              </TableCell>
              <TableCell className="text-muted-foreground">{credential.counsellor ?? '—'}</TableCell>
              <TableCell>
                <Badge variant="success" dot>
                  {credential.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}

const RECORD_BADGE: Record<string, 'success' | 'info' | 'warning' | 'destructive'> = {
  CREATED: 'success',
  REUSED: 'info',
  SKIPPED: 'warning',
  FAILED: 'destructive',
};

function RecordsPanel({ summary }: { summary: ImportSummary }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-16">Row</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Identifier</TableHead>
          <TableHead>Outcome</TableHead>
          <TableHead>Detail</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {summary.records.map((record, index) => (
          <TableRow key={`${record.record_type}-${record.identifier}-${index}`}>
            <TableCell className="font-mono text-muted-foreground">{record.source_row_number ?? '—'}</TableCell>
            <TableCell className="text-muted-foreground">{record.record_type === 'STUDENT' ? 'Student' : 'Counsellor'}</TableCell>
            <TableCell className="font-mono font-bold text-foreground">{record.identifier}</TableCell>
            <TableCell>
              <Badge variant={RECORD_BADGE[record.status] ?? 'secondary'}>{record.status}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">{record.message ?? '—'}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
