import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { StatCard } from '@/shared/components/ui/StatCard';
import { Button } from '@/shared/components/ui/Button';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage';
import { AcademicConfigPage } from '@/features/admin/pages/AcademicConfigPage';
import { StudentWorkspacePage } from '@/features/students/pages/StudentWorkspacePage';
import { SessionsPage } from '@/features/counselling/pages/SessionsPage';
import { NewSessionPage } from '@/features/counselling/pages/NewSessionPage';
import { RecordAttendancePage } from '@/features/attendance/pages/RecordAttendancePage';
import { MarksEntryPage } from '@/features/academics/pages/MarksEntryPage';
import { ParentCommunicationPage } from '@/features/parents/pages/ParentCommunicationPage';
import { NotificationCenterPage } from '@/features/notifications/pages/NotificationCenterPage';
import { ReportsPage } from '@/features/reports/pages/ReportsPage';
import { SettingsPage } from '@/features/settings/pages/SettingsPage';
import { AuditLogsPage } from '@/features/audit/pages/AuditLogsPage';

function DashboardPage() {
  return (
    <AppShell userRole="STUDENT" userName="Arjun Kumar">
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      <PageHeader
        title="Welcome back, Arjun 👋"
        subtitle="Current Semester: Semester 5 • Department: Computer Science"
        actions={<Button size="sm">View Workspace</Button>}
      />

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Overall Attendance"
          value="82.4%"
          change="+1.2%"
          trend="up"
          description="Above threshold (75%)"
        />
        <StatCard
          title="Current SGPA"
          value="8.4"
          change="+0.3"
          trend="up"
          description="Semester 4 SGPA"
        />
        <StatCard
          title="Active Backlogs"
          value="0"
          trend="neutral"
          description="All clear"
        />
        <StatCard
          title="Upcoming Session"
          value="Thu, 2 PM"
          description="With Dr. Priya Sharma"
        />
      </div>

      <div className="mt-8 rounded-lg border bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">🔴 Attention Required</h3>
        <p className="text-sm text-muted-foreground">
          No urgent attention items at this time. Keep up the good work!
        </p>
      </div>
    </AppShell>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardPage />,
  },
  {
    path: '/dashboard',
    element: <DashboardPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },
  {
    path: '/reset-password',
    element: <ResetPasswordPage />,
  },
  {
    path: '/admin/academic-config',
    element: <AcademicConfigPage />,
  },
  {
    path: '/students/:studentId',
    element: <StudentWorkspacePage />,
  },
  {
    path: '/my-workspace',
    element: <StudentWorkspacePage />,
  },
  {
    path: '/counselling/sessions',
    element: <SessionsPage />,
  },
  {
    path: '/counselling/new',
    element: <NewSessionPage />,
  },
  {
    path: '/attendance',
    element: <RecordAttendancePage />,
  },
  {
    path: '/attendance/record',
    element: <RecordAttendancePage />,
  },
  {
    path: '/academics',
    element: <MarksEntryPage />,
  },
  {
    path: '/academics/marks',
    element: <MarksEntryPage />,
  },
  {
    path: '/parent-communication',
    element: <ParentCommunicationPage />,
  },
  {
    path: '/notifications',
    element: <NotificationCenterPage />,
  },
  {
    path: '/reports',
    element: <ReportsPage />,
  },
  {
    path: '/settings',
    element: <SettingsPage />,
  },
  {
    path: '/admin/audit-logs',
    element: <AuditLogsPage />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
