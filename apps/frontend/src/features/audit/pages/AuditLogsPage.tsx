import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { settingsService, AuditLogItem } from '@/features/settings/services/settings.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Badge } from '@/shared/components/ui/Badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/shared/components/ui/Table';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { ShieldCheck, Filter } from 'lucide-react';

const ACTIONS = ['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PASSWORD_CHANGE', 'PASSWORD_RESET', 'APPROVE', 'REJECT'];

export function AuditLogsPage() {
  const [actionFilter, setActionFilter] = React.useState<string>('');

  const { data: logs, isLoading } = useQuery<AuditLogItem[]>({
    queryKey: ['admin', 'audit-logs', actionFilter],
    queryFn: () => settingsService.getAuditLogs(actionFilter || undefined),
  });

  return (
    <>
      <Breadcrumbs items={[{ label: 'Administration' }, { label: 'Security Audit Log' }]} />

      <PageHeader
        title="Security Audit Trail"
        subtitle="Immutable event log tracking administrative actions, user logins, and privilege updates"
      />

      <div className="my-6 flex items-center gap-3 p-4 rounded-xl border border-border/80 bg-card shadow-xs">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-semibold text-foreground">Filter Action Event:</span>
        <select
          className="h-9 rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        >
          <option value="">All Action Types</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      <div>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
        ) : !logs || logs.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No Security Logs Found"
            description="No audit records match the selected action filter criteria."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User Account</TableHead>
                <TableHead>Event Action</TableHead>
                <TableHead>Target Entity</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead className="text-right">Request Trace ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell className="font-semibold text-foreground">{log.user_email || 'System'}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono font-bold">{log.action}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{log.entity_type}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{log.ip_address || '—'}</TableCell>
                  <TableCell className="text-right font-mono text-[11px] text-muted-foreground">{log.request_id || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </>
  );
}
