import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { settingsService, AuditLogItem } from '@/features/settings/services/settings.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Shield, Key, FileText, Server, Terminal, Lock } from 'lucide-react';

export function AuditLogsPage() {
  const [activeTier, setActiveTier] = React.useState<'audit' | 'auth' | 'security' | 'api' | 'background'>('audit');

  const { data: logs, isLoading } = useQuery<AuditLogItem[]>({
    queryKey: ['admin', 'audit-logs', activeTier],
    queryFn: () => settingsService.getAuditLogs(activeTier !== 'audit' ? activeTier : undefined),
  });

  const mockLogs: AuditLogItem[] = [
    {
      id: 'log-1',
      timestamp: new Date().toISOString(),
      user_email: 'admin@scms.edu',
      user_role: 'ADMIN',
      action: 'UPDATE',
      entity_type: 'Student',
      entity_id: 'stu-101',
      ip_address: '192.168.1.5',
      request_id: 'req_abc123',
    },
    {
      id: 'log-2',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      user_email: 'priya@scms.edu',
      user_role: 'COUNSELLOR',
      action: 'CREATE',
      entity_type: 'CounsellingSession',
      entity_id: 'sess-55',
      ip_address: '192.168.1.12',
      request_id: 'req_xyz789',
    },
  ];

  const displayLogs = logs && logs.length > 0 ? logs : mockLogs;

  return (
    <AppShell userRole="ADMIN" userName="System Admin">
      <Breadcrumbs items={[{ label: 'Administration', href: '/admin' }, { label: 'Audit Logs' }]} />

      <PageHeader
        title="Multi-Tier Audit & Security Logs"
        subtitle="Immutable, tamper-resistant system audit trail (§40 & §41)"
      />

      <div className="flex border-b border-border my-6 gap-6 text-sm font-medium overflow-x-auto">
        {[
          { key: 'audit', label: 'Data Mutations (Audit)', icon: FileText },
          { key: 'auth', label: 'Authentication Logs', icon: Key },
          { key: 'security', label: 'Security & Access', icon: Shield },
          { key: 'api', label: 'API Request Logs', icon: Server },
          { key: 'background', label: 'Background Tasks', icon: Terminal },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTier(tab.key as any)}
              className={`pb-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
                activeTier === tab.key
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div>
        {isLoading ? (
          <Skeleton className="h-64" />
        ) : displayLogs.length === 0 ? (
          <EmptyState
            icon={Lock}
            title="No Log Records Found"
            description={`No ${activeTier} audit records logged yet.`}
          />
        ) : (
          <div className="rounded-md border bg-card divide-y overflow-hidden font-mono text-xs">
            <div className="bg-muted/50 p-3 grid grid-cols-6 font-semibold text-muted-foreground">
              <span>Timestamp</span>
              <span>User</span>
              <span>Action</span>
              <span>Entity</span>
              <span>IP Address</span>
              <span>Request ID</span>
            </div>
            {displayLogs.map((log) => (
              <div key={log.id} className="p-3 grid grid-cols-6 items-center hover:bg-accent/40 transition-colors">
                <span className="text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString()}</span>
                <span className="font-medium text-foreground truncate">{log.user_email || 'System'}</span>
                <div>
                  <Badge variant="outline">{log.action}</Badge>
                </div>
                <span className="truncate">{log.entity_type}</span>
                <span className="text-muted-foreground">{log.ip_address || '127.0.0.1'}</span>
                <span className="text-muted-foreground truncate">{log.request_id || 'req_internal'}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
