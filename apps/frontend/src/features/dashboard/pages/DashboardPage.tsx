import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { api } from '@/shared/lib/axios';
import { studentService, Student360Data } from '@/features/students/services/student.service';
import { notificationService } from '@/features/notifications/services/notification.service';
import { CounsellorDashboard } from '../components/CounsellorDashboard';
import {
  LayoutDashboard,
  Bell,
  AlertTriangle,
  Sparkles,
  Calendar,
  Award,
  Users,
  MessageSquare,
  PhoneCall,
  BookOpen,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Zap,
} from 'lucide-react';

interface QuickAction {
  label: string;
  to: string;
  icon: React.ElementType;
  permission: string;
}

// Every staff shortcut is gated on the underlying permission, so no role is
// ever shown a button that would bounce it to /forbidden.
const STAFF_QUICK_ACTIONS: QuickAction[] = [
  { label: 'User Directory', to: '/admin/users', icon: Users, permission: 'user.manage' },
  { label: 'Counselling Sessions', to: '/counselling/sessions', icon: MessageSquare, permission: 'counselling.read' },
  { label: 'Record Attendance', to: '/attendance', icon: Calendar, permission: 'attendance.create' },
  { label: 'Marks Entry', to: '/academics/marks', icon: BookOpen, permission: 'marks.create' },
  { label: 'Parent Interactions', to: '/parent-communication', icon: PhoneCall, permission: 'parent_communication.read' },
  { label: 'Reports Catalog', to: '/reports', icon: Award, permission: 'report.generate' },
];

export function DashboardPage() {
  const { user, hasPermission } = useAuth();
  const firstName = user?.full_name?.split(' ')[0] ?? 'there';
  const role = user?.roles[0] ?? 'STUDENT';
  const isStudent = user?.roles.includes('STUDENT') ?? false;
  // A counsellor's landing page is their caseload summary, not the generic
  // shortcut grid. Admins who also hold COUNSELLOR keep the admin view.
  const isCounsellor =
    (user?.roles.includes('COUNSELLOR') ?? false) &&
    !(user?.roles.some((r) => ['ADMIN', 'SUPER_ADMIN'].includes(r)) ?? false);

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationService.getUnreadCount,
  });

  const { data: isHealthy } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const res = await api.get('/health/ready');
      return res.data?.status === 'healthy';
    },
    retry: false,
    staleTime: 30_000,
    refetchInterval: 60_000,
    enabled: !isStudent,
  });

  const quickActions = STAFF_QUICK_ACTIONS.filter((a) => hasPermission(a.permission));

  const { data: workspace, isLoading: workspaceLoading } = useQuery<Student360Data>({
    queryKey: ['students', 'me', 'workspace'],
    queryFn: studentService.getMyWorkspace,
    enabled: isStudent,
  });

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  // A counsellor's landing page is a workspace, not a report: it brings its own
  // compact header (greeting, live counts, quick actions) and needs the vertical
  // space the hero banner used to occupy. Notifications live in the top-nav bell
  // for every role, so nothing is lost by dropping the banner here.
  if (isCounsellor) {
    return (
      <>
        <Breadcrumbs items={[{ label: 'Counsellor Workspace' }]} />
        <CounsellorDashboard />
      </>
    );
  }

  return (
    <>
      <Breadcrumbs items={[{ label: 'Executive Dashboard' }]} />

      {/* Hero Welcome Banner Card */}
      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-r from-navy-900 via-navy-800 to-navy-900 text-white p-6 md:p-8 mb-8 shadow-xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-brand-500/25 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-brand-200 border-brand-300/30 bg-brand-500/20">
                {role.replace('_', ' ')}
              </Badge>
              <span className="text-xs text-slate-400 font-mono">{todayStr}</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white">
              Welcome back, {firstName} 👋
            </h1>
            <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
              Monitor attendance thresholds, counselling task lists, and academic alerts across your workspace.
            </p>
          </div>

          {/* Notifications deliberately absent — the top-nav bell is the single
              place they are surfaced, so there is one unread count, not two. */}
          {isStudent && (
            <div className="flex items-center gap-3 shrink-0">
              <Button asChild size="sm" className="font-bold">
                <Link to="/student-360/personal">
                  Open 360 Portal <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          )}
        </div>
      </div>

      {isStudent ? (
        workspaceLoading ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Skeleton className="h-32 rounded-2xl" />
              <Skeleton className="h-32 rounded-2xl" />
              <Skeleton className="h-32 rounded-2xl" />
              <Skeleton className="h-32 rounded-2xl" />
            </div>
            <Skeleton className="h-48 rounded-2xl" />
          </div>
        ) : workspace ? (
          <div className="space-y-8">
            {/* KPI Stat Cards Grid */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {workspace.stats.map((stat, idx) => {
                const icons = [Award, Calendar, MessageSquare, Sparkles];
                return (
                  <StatCard
                    key={idx}
                    title={stat.title}
                    value={stat.value}
                    change={stat.change}
                    trend={stat.trend as any}
                    description={stat.description}
                    icon={icons[idx % icons.length]}
                  />
                );
              })}
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Attention Required Card */}
              <Card className="lg:col-span-2">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Attention & Actions Required
                    </CardTitle>
                    <CardDescription>
                      Critical alerts needing immediate response or follow-up
                    </CardDescription>
                  </div>
                  <Badge variant="warning">{workspace.attention_items.length} Pending</Badge>
                </CardHeader>
                <CardContent className="pt-2">
                  {workspace.attention_items.length > 0 ? (
                    <div className="space-y-2.5">
                      {workspace.attention_items.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 rounded-xl border border-border/70 bg-muted/30 p-3.5 text-xs text-foreground hover:bg-accent/50 transition-colors"
                        >
                          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-600 font-bold text-[10px]">
                            {idx + 1}
                          </span>
                          <span className="flex-1 font-medium leading-relaxed">{item}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center text-center p-6 border border-dashed border-border/60 rounded-xl">
                      <CheckCircle2 className="h-8 w-8 text-emerald-500 mb-2" />
                      <p className="text-xs font-bold text-foreground">All caught up!</p>
                      <p className="text-[11px] text-muted-foreground">No urgent attention items at this time.</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Navigation Panel */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Workspace Shortcuts</CardTitle>
                  <CardDescription>Direct action access</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 pt-2">
                  <Button asChild variant="outline" className="w-full justify-between text-xs font-semibold" size="sm">
                    <Link to="/student-360/personal">
                      <span className="flex items-center gap-2">
                        <Users className="h-3.5 w-3.5 text-brand-500" />
                        My 360 Portal
                      </span>
                      <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="mt-6">
            <EmptyState
              icon={LayoutDashboard}
              title="No student record linked"
              description="Your account isn't linked to an active student record. Contact your institutional administrator."
            />
          </div>
        )
      ) : (
        /* Staff / Admin Dashboard Overview */
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Unread Notifications"
              value={unreadCount !== undefined ? String(unreadCount) : '0'}
              description="Pending alerts & reminders"
              icon={Bell}
            />
            <StatCard
              title="System Status"
              value={isHealthy === undefined ? 'Checking…' : isHealthy ? 'Operational' : 'Degraded'}
              description={isHealthy === false ? 'A backend service is unavailable' : 'Core services responding'}
              icon={ShieldCheck}
              trend={isHealthy === false ? 'down' : 'up'}
            />
          </div>

          {quickActions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Zap className="h-4 w-4 text-brand-500" />
                  Quick Actions
                </CardTitle>
                <CardDescription>
                  Operational shortcuts available to your role ({role.replace('_', ' ')}).
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {quickActions.map((action) => {
                    const Icon = action.icon;
                    return (
                      <Button key={action.to} asChild variant="outline" size="sm" className="justify-start font-semibold">
                        <Link to={action.to}>
                          <Icon className="mr-2 h-4 w-4 text-brand-500" />
                          {action.label}
                        </Link>
                      </Button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </>
  );
}
