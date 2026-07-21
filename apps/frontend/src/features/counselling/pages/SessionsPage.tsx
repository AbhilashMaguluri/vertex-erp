import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { counsellingService, CounsellingSession, ActionItem } from '../services/counselling.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { MessageSquare, Plus, CheckCircle, Clock } from 'lucide-react';

export function SessionsPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState<'sessions' | 'follow-ups'>('sessions');

  const { data: sessions, isLoading: sessionsLoading } = useQuery<CounsellingSession[]>({
    queryKey: ['counselling', 'sessions'],
    queryFn: () => counsellingService.getSessions(),
    enabled: activeTab === 'sessions',
  });

  const { data: followUps, isLoading: followUpsLoading } = useQuery<ActionItem[]>({
    queryKey: ['counselling', 'follow-ups'],
    queryFn: () => counsellingService.getFollowUps(),
    enabled: activeTab === 'follow-ups',
  });

  return (
    <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
      <Breadcrumbs items={[{ label: 'Counselling Workspace', href: '/counselling' }, { label: 'Sessions' }]} />

      <PageHeader
        title="Counselling Sessions & Follow-ups"
        subtitle="Manage counselling records, session observations, and action item tracking"
        actions={
          <Button size="sm" onClick={() => navigate('/counselling/new')}>
            <Plus className="mr-1.5 h-4 w-4" /> Record New Session
          </Button>
        }
      />

      <div className="flex border-b border-border my-6 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('sessions')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'sessions'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Sessions History
        </button>

        <button
          onClick={() => setActiveTab('follow-ups')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'follow-ups'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Clock className="h-4 w-4" />
          Follow-up Action Items
        </button>
      </div>

      {activeTab === 'sessions' && (
        <div>
          {sessionsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="No Counselling Sessions Recorded"
              description="Record your first session with an assigned student."
              actionLabel="Record Session"
              onAction={() => navigate('/counselling/new')}
            />
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div key={session.id} className="rounded-lg border bg-card p-4 shadow-2xs hover:border-primary/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">Session #{session.id.slice(0, 8)}</span>
                      <Badge variant="outline">{session.session_type}</Badge>
                      <Badge variant="secondary">{session.mode}</Badge>
                    </div>
                    <time className="text-xs text-muted-foreground">{session.session_date}</time>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{session.observations}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'follow-ups' && (
        <div>
          {followUpsLoading ? (
            <Skeleton className="h-32" />
          ) : !followUps || followUps.length === 0 ? (
            <EmptyState
              icon={CheckCircle}
              title="No Pending Action Items"
              description="All follow-up tasks are completed or none assigned."
            />
          ) : (
            <div className="space-y-3">
              {followUps.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg bg-card">
                  <div>
                    <p className="text-sm font-medium">{item.description}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Due: {item.due_date}</p>
                  </div>
                  <Badge variant={item.status === 'OVERDUE' ? 'danger' : 'warning'}>{item.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
