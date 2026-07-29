import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { counsellingService, CounsellingSession, ActionItem } from '../services/counselling.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { MessageSquare, Plus, CheckCircle2, Clock, Calendar } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

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
    <>
      <Breadcrumbs items={[{ label: 'Counselling' }, { label: 'Sessions & Tasks' }]} />

      <PageHeader
        title="Counselling Sessions & Follow-ups"
        subtitle="Record session notes, student observations, risk flags, and follow-up action items"
        actions={
          <Button size="sm" onClick={() => navigate('/counselling/new')}>
            <Plus className="mr-1.5 h-4 w-4" /> Record New Session
          </Button>
        }
      />

      <div className="flex border-b border-border my-6 gap-2 text-xs font-semibold select-none pb-1">
        <button
          onClick={() => setActiveTab('sessions')}
          className={cn(
            'px-3.5 py-2.5 rounded-lg flex items-center gap-2 transition-all cursor-pointer',
            activeTab === 'sessions'
              ? 'bg-primary text-primary-foreground font-bold shadow-xs'
              : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          )}
        >
          <MessageSquare className="h-4 w-4" />
          Sessions History
        </button>

        <button
          onClick={() => setActiveTab('follow-ups')}
          className={cn(
            'px-3.5 py-2.5 rounded-lg flex items-center gap-2 transition-all cursor-pointer',
            activeTab === 'follow-ups'
              ? 'bg-primary text-primary-foreground font-bold shadow-xs'
              : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          )}
        >
          <Clock className="h-4 w-4" />
          Follow-up Action Items
        </button>
      </div>

      {activeTab === 'sessions' && (
        <div>
          {sessionsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 rounded-xl" />
              <Skeleton className="h-24 rounded-xl" />
              <Skeleton className="h-24 rounded-xl" />
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="No Counselling Sessions Recorded"
              description="Record your first session with an assigned student to track observations and guidance."
              actionLabel="Record Session"
              onAction={() => navigate('/counselling/new')}
            />
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <Card key={session.id} className="hover:border-primary/40">
                  <CardContent className="p-5 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-foreground">Session #{session.id.slice(0, 8)}</span>
                        <Badge variant="default">{session.session_type}</Badge>
                        <Badge variant="outline">{session.mode}</Badge>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{session.session_date}</span>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {session.observations}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'follow-ups' && (
        <div>
          {followUpsLoading ? (
            <Skeleton className="h-48 rounded-xl" />
          ) : !followUps || followUps.length === 0 ? (
            <EmptyState
              icon={CheckCircle2}
              title="No Pending Action Items"
              description="All follow-up tasks and student check-ins are up to date."
            />
          ) : (
            <div className="space-y-3">
              {followUps.map((item) => (
                <Card key={item.id}>
                  <CardContent className="p-4 flex items-center justify-between gap-4">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-foreground">{item.description}</p>
                      <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" /> Due by: {item.due_date}
                      </p>
                    </div>
                    <Badge variant={item.status === 'OVERDUE' ? 'destructive' : 'warning'}>
                      {item.status}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
