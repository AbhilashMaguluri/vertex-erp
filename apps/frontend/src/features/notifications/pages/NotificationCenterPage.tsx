import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationService, NotificationItem } from '../services/notification.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Bell, CheckCheck, AlertTriangle, AlertOctagon, Info } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export function NotificationCenterPage() {
  const queryClient = useQueryClient();
  const [filterUnread, setFilterUnread] = React.useState(false);

  const { data: notifications, isLoading } = useQuery<NotificationItem[]>({
    queryKey: ['notifications', filterUnread],
    queryFn: () => notificationService.getNotifications(filterUnread),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const displayNotifs = notifications ?? [];

  return (
    <>
      <Breadcrumbs items={[{ label: 'Notification Center' }]} />

      <PageHeader
        title="Notification Center"
        subtitle="Stay informed with real-time academic alerts, session reminders, and system announcements"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            isLoading={markAllReadMutation.isPending}
          >
            <CheckCheck className="mr-1.5 h-4 w-4 text-emerald-600" /> Mark All as Read
          </Button>
        }
      />

      <div className="flex border-b border-border my-6 gap-2 text-xs font-semibold select-none pb-1">
        <button
          onClick={() => setFilterUnread(false)}
          className={cn(
            'px-3.5 py-2.5 rounded-lg transition-all cursor-pointer',
            !filterUnread
              ? 'bg-primary text-primary-foreground font-bold shadow-xs'
              : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          )}
        >
          All Notifications
        </button>
        <button
          onClick={() => setFilterUnread(true)}
          className={cn(
            'px-3.5 py-2.5 rounded-lg transition-all cursor-pointer',
            filterUnread
              ? 'bg-primary text-primary-foreground font-bold shadow-xs'
              : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          )}
        >
          Unread Only
        </button>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 rounded-xl" />
            <Skeleton className="h-24 rounded-xl" />
          </div>
        ) : displayNotifs.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="All Caught Up!"
            description="You have zero unread alerts or pending notifications at this time."
          />
        ) : (
          displayNotifs.map((item) => (
            <Card
              key={item.id}
              className={cn(
                'transition-all duration-150',
                !item.is_read ? 'border-primary/40 bg-card shadow-xs' : 'opacity-75 bg-muted/20'
              )}
            >
              <CardContent className="p-4 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="mt-1 shrink-0">
                    {item.priority === 'URGENT' && (
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-500/10 text-rose-600">
                        <AlertOctagon className="h-5 w-5" />
                      </div>
                    )}
                    {item.priority === 'HIGH' && (
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
                        <AlertTriangle className="h-5 w-5" />
                      </div>
                    )}
                    {(item.priority === 'NORMAL' || item.priority === 'LOW') && (
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500/10 text-sky-600">
                        <Info className="h-5 w-5" />
                      </div>
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-bold text-foreground">{item.title}</h4>
                      <Badge
                        variant={
                          item.priority === 'URGENT'
                            ? 'destructive'
                            : item.priority === 'HIGH'
                            ? 'warning'
                            : 'outline'
                        }
                      >
                        {item.priority}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{item.message}</p>
                    <time className="block text-[10px] font-mono text-muted-foreground/80 pt-1">
                      {new Date(item.created_at).toLocaleString()}
                    </time>
                  </div>
                </div>

                {!item.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markReadMutation.mutate(item.id)}
                    className="text-xs text-primary hover:bg-primary/10 shrink-0"
                  >
                    Mark Read
                  </Button>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </>
  );
}
