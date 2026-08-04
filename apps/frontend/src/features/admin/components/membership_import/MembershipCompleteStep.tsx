import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle2,
  Download,
  FileSpreadsheet,
  KeyRound,
  RotateCcw,
  ShieldAlert,
  Trash2,
  Eye,
  EyeOff,
  Link2,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/Table';
import { membershipImportService } from '../../services/membershipImport.service';

interface MembershipCompleteStepProps {
  batchId: string;
  onStartAnother: () => void;
}

export function MembershipCompleteStep({ batchId, onStartAnother }: MembershipCompleteStepProps) {
  const queryClient = useQueryClient();
  const [showPasswords, setShowPasswords] = React.useState(false);
  const [tab, setTab] = React.useState<'credentials' | 'records'>('credentials');

  const { data: summary, isLoading } = useQuery({
    queryKey: ['admin', 'membership-imports', batchId, 'summary'],
    queryFn: () => membershipImportService.getSummary(batchId),
  });

  const { data: credentials } = useQuery({
    queryKey: ['admin', 'membership-imports', batchId, 'credentials'],
    queryFn: () => membershipImportService.getCredentials(batchId, 100),
    enabled: Boolean(summary?.credentials_available),
    retry: false,
  });

  const purge = useMutation({
    mutationFn: () => membershipImportService.purgeCredentials(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'membership-imports'] });
    },
  });

  if (isLoading || !summary) {
    return <Skeleton className="h-96 w-full rounded-2xl" />;
  }

  const credentialsAvailable = summary.credentials_available && Boolean(credentials?.length);

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
              <h2 className="text-lg font-bold text-foreground">Membership Import Complete!</h2>
              <p className="text-xs text-muted-foreground">
                {summary.memberships_created} new memberships created, {summary.students_created} student accounts provisioned.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => membershipImportService.downloadReport(batchId)}>
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
          <p className="text-xs text-muted-foreground">Students Created</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{summary.students_created}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Students Reused</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{summary.students_reused}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Memberships Created</p>
          <p className="mt-1 text-2xl font-bold text-primary">{summary.memberships_created}</p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Memberships Updated</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{summary.memberships_updated}</p>
        </div>
      </div>

      {/* Credentials Banner */}
      {credentialsAvailable && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                <div>
                  <CardTitle className="text-base text-amber-900 dark:text-amber-200">
                    Temporary Passwords Generated ({credentials?.length})
                  </CardTitle>
                  <CardDescription className="text-amber-800/80 dark:text-amber-300/80 text-xs">
                    Download credentials workbook now. Purge when finished to prevent exposure.
                  </CardDescription>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => membershipImportService.downloadCredentials(batchId)}
                >
                  <Download className="mr-1.5 h-4 w-4" /> Download Excel
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => purge.mutate()}
                  disabled={purge.isPending}
                >
                  <Trash2 className="mr-1.5 h-4 w-4" /> Purge Credentials
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}

      {/* Detail tabs */}
      <Card>
        <CardHeader>
          <div className="flex gap-2 border-b border-border pb-3">
            {credentialsAvailable && (
              <button
                onClick={() => setTab('credentials')}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold ${
                  tab === 'credentials' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <KeyRound className="h-3.5 w-3.5" /> Credentials ({credentials?.length})
              </button>
            )}
            <button
              onClick={() => setTab('records')}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold ${
                tab === 'records' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Link2 className="h-3.5 w-3.5" /> Audit Log ({summary.records.length})
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {tab === 'credentials' && credentialsAvailable && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <Button variant="ghost" size="sm" onClick={() => setShowPasswords(!showPasswords)}>
                  {showPasswords ? <EyeOff className="mr-1.5 h-3.5 w-3.5" /> : <Eye className="mr-1.5 h-3.5 w-3.5" />}
                  {showPasswords ? 'Hide passwords' : 'Show passwords'}
                </Button>
              </div>
              <div className="max-h-[350px] overflow-auto rounded-lg border border-border/30">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Roll Number</TableHead>
                      <TableHead>Full Name</TableHead>
                      <TableHead>Username</TableHead>
                      <TableHead>Temp Password</TableHead>
                      <TableHead>Counselor Email</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {credentials?.map((c) => (
                      <TableRow key={c.roll_number}>
                        <TableCell className="font-mono text-xs font-bold">{c.roll_number}</TableCell>
                        <TableCell className="text-xs">{c.full_name}</TableCell>
                        <TableCell className="font-mono text-xs">{c.username}</TableCell>
                        <TableCell className="font-mono text-xs font-bold text-rose-600">
                          {showPasswords ? c.temporary_password : '••••••••'}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{c.counselor_email}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {tab === 'records' && (
            <div className="max-h-[350px] overflow-auto rounded-lg border border-border/30">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Identifier</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Message</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.records.map((r, idx) => (
                    <TableRow key={`${r.identifier}-${idx}`}>
                      <TableCell className="text-xs font-semibold">{r.record_type}</TableCell>
                      <TableCell className="font-mono text-xs">{r.identifier}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            r.status === 'CREATED' ? 'success' :
                            r.status === 'REUSED' ? 'info' :
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
