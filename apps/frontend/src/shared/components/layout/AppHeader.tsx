import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell,
  LogOut,
  Search,
  User as UserIcon,
  Settings as SettingsIcon,
  KeyRound,
  ChevronDown,
  CheckCheck,
  AlertTriangle,
  AlertOctagon,
  Info,
  Inbox,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import {
  notificationService,
  NotificationItem,
  CATEGORY_LABELS,
} from '@/features/notifications/services/notification.service';
import { cn } from '@/shared/utils/cn';

interface AppHeaderProps {
  userName?: string;
  userRole?: string;
  onLogout?: () => void;
  onSearchClick?: () => void;
}

function useClickOutside(onOutside: () => void) {
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onOutside();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onOutside]);
  return ref;
}

function CategoryChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'shrink-0 cursor-pointer rounded-full px-2.5 py-1 text-[10px] font-bold transition-colors',
        active
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted/60 text-muted-foreground hover:bg-accent hover:text-foreground'
      )}
    >
      {label}
      {count ? <span className="ml-1 opacity-80">{count}</span> : null}
    </button>
  );
}

function priorityIcon(priority: string) {
  if (priority === 'URGENT') return <AlertOctagon className="h-4 w-4" />;
  if (priority === 'HIGH') return <AlertTriangle className="h-4 w-4" />;
  return <Info className="h-4 w-4" />;
}

function priorityClasses(priority: string) {
  if (priority === 'URGENT') return 'bg-rose-500/10 text-rose-600';
  if (priority === 'HIGH') return 'bg-amber-500/10 text-amber-600';
  return 'bg-sky-500/10 text-sky-600';
}

export function AppHeader({
  userName = 'User',
  userRole = 'STUDENT',
  onLogout,
  onSearchClick,
}: AppHeaderProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [openMenu, setOpenMenu] = React.useState<'notifications' | 'profile' | null>(null);

  const bellRef = useClickOutside(() => setOpenMenu((m) => (m === 'notifications' ? null : m)));
  const profileRef = useClickOutside(() => setOpenMenu((m) => (m === 'profile' ? null : m)));

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationService.getUnreadCount,
    refetchInterval: 60_000,
  });

  // null = "All". Category lives in local state rather than the URL: the bell
  // is a transient preview, not a navigable view.
  const [category, setCategory] = React.useState<string | null>(null);

  const { data: recentNotifications, isLoading: isLoadingRecent } = useQuery<NotificationItem[]>({
    queryKey: ['notifications', 'recent', category],
    queryFn: () => notificationService.getNotifications(false, category ?? undefined),
    enabled: openMenu === 'notifications',
    staleTime: 15_000,
  });

  const { data: summary } = useQuery({
    queryKey: ['notifications', 'summary'],
    queryFn: notificationService.getSummary,
    enabled: openMenu === 'notifications',
    staleTime: 15_000,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const hasUnread = !!unreadCount && unreadCount > 0;
  const recentList = (recentNotifications ?? []).slice(0, 6);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  const goToNotification = (item: NotificationItem) => {
    if (!item.is_read) markReadMutation.mutate(item.id);
    setOpenMenu(null);
    navigate('/notifications');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/80 bg-card/85 px-4 md:px-6 backdrop-blur-md shadow-2xs transition-colors">
      {/* Search Bar — only rendered for roles that can actually search
          (onSearchClick supplied). Hidden entirely for students. */}
      <div className="flex items-center gap-4">
        {onSearchClick && (
          <button
            onClick={onSearchClick}
            className="flex h-9 w-64 md:w-80 items-center justify-between rounded-lg border border-input bg-background/60 px-3 text-xs text-muted-foreground transition-all hover:border-primary/40 hover:bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <div className="flex items-center gap-2">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <span>Search students, users...</span>
            </div>
            <kbd className="hidden sm:inline-flex h-5 items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ⌘K
            </kbd>
          </button>
        )}
      </div>

      {/* Right User Navigation */}
      <div className="flex items-center gap-3">
        {/* Notification Bell */}
        <div className="relative" ref={bellRef}>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setOpenMenu((m) => (m === 'notifications' ? null : 'notifications'))}
            className="relative text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
            title={hasUnread ? `${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}` : 'Notifications'}
          >
            <Bell className="h-4 w-4" />
            {hasUnread && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white ring-2 ring-card">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Button>

          {openMenu === 'notifications' && (
            <div className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] rounded-2xl border border-border/80 bg-card shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95 duration-150">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border/70">
                <span className="text-xs font-bold text-foreground">Notifications</span>
                {hasUnread && (
                  <button
                    onClick={() => markAllReadMutation.mutate()}
                    disabled={markAllReadMutation.isPending}
                    className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline disabled:opacity-50"
                  >
                    <CheckCheck className="h-3 w-3" /> Mark all read
                  </button>
                )}
              </div>

              {/* Category filter. Only categories that actually have
                  notifications are offered, so the rail never shows a tab that
                  leads to an empty list. */}
              <div className="flex gap-1 overflow-x-auto border-b border-border/70 px-2 py-2">
                <CategoryChip
                  label="All"
                  count={summary?.total_count}
                  active={category === null}
                  onClick={() => setCategory(null)}
                />
                {(summary?.categories ?? [])
                  .filter((c) => c.total > 0)
                  .map((c) => (
                    <CategoryChip
                      key={c.category}
                      label={CATEGORY_LABELS[c.category] ?? c.category}
                      count={c.unread || undefined}
                      active={category === c.category}
                      onClick={() => setCategory(c.category)}
                    />
                  ))}
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-border/60">
                {isLoadingRecent ? (
                  <div className="p-6 text-center text-xs text-muted-foreground">Loading…</div>
                ) : recentList.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 p-8 text-center">
                    <Inbox className="h-6 w-6 text-muted-foreground/50" />
                    <p className="text-xs text-muted-foreground">You're all caught up.</p>
                  </div>
                ) : (
                  recentList.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => goToNotification(item)}
                      className={cn(
                        'flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent',
                        !item.is_read && 'bg-primary/5'
                      )}
                    >
                      <div className={cn('mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg', priorityClasses(item.priority))}>
                        {priorityIcon(item.priority)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <p className="truncate text-xs font-bold text-foreground">{item.title}</p>
                          {!item.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />}
                        </div>
                        <p className="line-clamp-2 text-[11px] text-muted-foreground leading-relaxed">{item.message}</p>
                        <time className="mt-0.5 block text-[10px] font-mono text-muted-foreground/70">
                          {new Date(item.created_at).toLocaleString()}
                        </time>
                      </div>
                    </button>
                  ))
                )}
              </div>

              <button
                onClick={() => {
                  setOpenMenu(null);
                  navigate('/notifications');
                }}
                className="block w-full border-t border-border/70 px-4 py-2.5 text-center text-xs font-bold text-primary hover:bg-accent"
              >
                View All Notifications
              </button>
            </div>
          )}
        </div>

        <div className="h-5 w-px bg-border/80" />

        {/* User Info & Avatar / Profile Dropdown */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setOpenMenu((m) => (m === 'profile' ? null : 'profile'))}
            className="flex items-center gap-2.5 rounded-xl px-1.5 py-1 transition-colors hover:bg-accent cursor-pointer"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold text-xs shadow-xs border border-primary/20">
              {userName ? getInitials(userName) : <UserIcon className="h-4 w-4" />}
            </div>

            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-bold text-foreground leading-tight">{userName}</span>
              <div className="mt-0.5">
                <Badge variant="outline" className="text-[9px] py-0 px-1.5 font-bold uppercase tracking-wider">
                  {userRole}
                </Badge>
              </div>
            </div>
            <ChevronDown className={cn('hidden sm:block h-3.5 w-3.5 text-muted-foreground transition-transform', openMenu === 'profile' && 'rotate-180')} />
          </button>

          {openMenu === 'profile' && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-border/80 bg-card shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95 duration-150">
              <div className="px-4 py-3 border-b border-border/70">
                <p className="truncate text-xs font-bold text-foreground">{userName}</p>
                <p className="truncate text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">{userRole}</p>
              </div>

              <div className="py-1.5">
                <button
                  onClick={() => {
                    setOpenMenu(null);
                    navigate('/settings', { state: { section: 'profile' } });
                  }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-xs font-semibold text-foreground hover:bg-accent"
                >
                  <UserIcon className="h-3.5 w-3.5 text-muted-foreground" /> My Profile
                </button>
                <button
                  onClick={() => {
                    setOpenMenu(null);
                    navigate('/settings', { state: { section: 'appearance' } });
                  }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-xs font-semibold text-foreground hover:bg-accent"
                >
                  <SettingsIcon className="h-3.5 w-3.5 text-muted-foreground" /> Settings
                </button>
                <button
                  onClick={() => {
                    setOpenMenu(null);
                    navigate('/change-password');
                  }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-xs font-semibold text-foreground hover:bg-accent"
                >
                  <KeyRound className="h-3.5 w-3.5 text-muted-foreground" /> Change Password
                </button>
              </div>

              <div className="border-t border-border/70 py-1.5">
                <button
                  onClick={() => {
                    setOpenMenu(null);
                    onLogout?.();
                  }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-500/10"
                >
                  <LogOut className="h-3.5 w-3.5" /> Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
