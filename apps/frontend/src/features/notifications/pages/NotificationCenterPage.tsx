import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationService, NotificationItem } from '../services/notification.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Bell, CheckCheck, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

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

  const mockNotifs: NotificationItem[] = [
    {
      id: 'notif-1',
      user_id: 'u-1',
      type: 'ATTENDANCE_ALERT',
      priority: 'URGENT',
      title: 'Attendance Critical Alert',
      message: 'Student Arjun Kumar (21CS101) attendance dropped below 75% in Mathematics.',
      is_read: false,
      created_at: new Date().toISOString(),
    },
    {
      id: 'notif-2',
      user_id: 'u-1',
      type: 'FOLLOW_UP_REMINDER',
      priority: 'HIGH',
      title: 'Follow-up Session Due Today',
      message: 'You have a scheduled follow-up with Rahul Verma at 2:00 PM.',
      is_read: false,
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    },
    {
      id: 'notif-3',
      user_id: 'u-1',
      type: 'SYSTEM',
      priority: 'NORMAL',
      title: 'Monthly Counselling Compliance Generated',
      message: 'Your monthly report for October 2026 is ready for download.',
      is_read: true,
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ];

  const displayNotifs = notifications && notifications.length > 0 ? notifications : mockNotifs;

  return (
    <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
      <Breadcrumbs items={[{ label: 'Notifications Center' }]} />

      <PageHeader
        title="Notification Center"
        subtitle="Stay updated on attendance alerts, follow-up reminders, and system announcements (§22)"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
          >
            <CheckCheck className="mr-1.5 h-4 w-4" /> Mark All Read
          </Button>
        }
      />

      <div className="mt-6 flex items-center justify-between border-b border-border pb-3">
        <div className="flex gap-4 text-xs font-semibold">
          <button
            onClick={() => setFilterUnread(false)}
            className={`pb-1 transition-colors ${!filterUnread ? 'text-primary border-b-2 border-primary' : 'text-muted-foreground'}`}
          >
            All Notifications
          </button>
          <button
            onClick={() => setFilterUnread(true)}
            className={`pb-1 transition-colors ${filterUnread ? 'text-primary border-b-2 border-primary' : 'text-muted-foreground'}`}
          >
            Unread Only
          </button>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {isLoading ? (
          <Skeleton className="h-40" />
        ) : displayNotifs.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="No Notifications"
            description="You are all caught up! No unread alerts or reminders."
          />
        ) : (
          displayNotifs.map((item) => (
            <div
              key={item.id}
              className={`flex items-start justify-between rounded-lg border p-4 shadow-2xs transition-colors ${
                !item.is_read ? 'bg-card border-primary/40 font-medium' : 'bg-muted/30 border-border text-muted-foreground'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {item.priority === 'URGENT' && <AlertOctagon className="h-5 w-5 text-red-600" />}
                  {item.priority === 'HIGH' && <AlertTriangle className="h-5 w-5 text-amber-600" />}
                  {(item.priority === 'NORMAL' || item.priority === 'LOW') && <Info className="h-5 w-5 text-blue-600" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-foreground">{item.title}</h4>
                    <Badge variant={item.priority === 'URGENT' ? 'danger' : item.priority === 'HIGH' ? 'warning' : 'outline'}>
                      {item.priority}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{item.message}</p>
                  <time className="mt-2 block text-[10px] text-muted-foreground">
                    {new Date(item.created_at).toLocaleString()}
                  </time>
                </div>
              </div>

              {!item.is_read && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => markReadMutation.mutate(item.id)}
                  className="text-xs text-primary hover:underline shrink-0"
                >
                  Mark Read
                </Button>
              )}
            </div>
          ))
        )}
      </div>
    </AppShell>
  );
}
