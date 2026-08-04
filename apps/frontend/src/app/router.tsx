import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppLayout } from '@/shared/components/layout/AppLayout';
import { ProtectedRoute } from '@/features/auth/routing/ProtectedRoute';
import { GuestRoute } from '@/features/auth/routing/GuestRoute';
import { RequirePasswordChange } from '@/features/auth/routing/RequirePasswordChange';
import { PermissionGuard } from '@/features/auth/routing/PermissionGuard';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { ForgotPasswordPage } from '@/features/auth/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@/features/auth/pages/ResetPasswordPage';
import { ChangePasswordPage } from '@/features/auth/pages/ChangePasswordPage';
import { ForbiddenPage } from '@/features/auth/pages/ForbiddenPage';
import { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
import { SessionExpiredPage } from '@/features/auth/pages/SessionExpiredPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { AcademicConfigPage } from '@/features/admin/pages/AcademicConfigPage';
import { AssessmentConfigPage } from '@/features/admin/pages/AssessmentConfigPage';
import { UserManagementPage } from '@/features/admin/pages/UserManagementPage';
import { OfficeImportPage } from '@/features/admin/pages/OfficeImportPage';
import { MembershipImportPage } from '@/features/admin/pages/MembershipImportPage';
import { StudentWorkspacePage } from '@/features/students/pages/StudentWorkspacePage';
import { MyProfilePage } from '@/features/students/pages/MyProfilePage';
import { MyStudentsPage } from '@/features/students/pages/MyStudentsPage';
import { SessionsPage } from '@/features/counselling/pages/SessionsPage';
import { NewSessionPage } from '@/features/counselling/pages/NewSessionPage';
import { RecordAttendancePage } from '@/features/attendance/pages/RecordAttendancePage';
import { AttendanceImportPage } from '@/features/attendance/pages/AttendanceImportPage';
import { MarksEntryPage } from '@/features/academics/pages/MarksEntryPage';
import { MarksImportPage } from '@/features/academics/pages/MarksImportPage';
import { ParentCommunicationPage } from '@/features/parents/pages/ParentCommunicationPage';
import { NotificationCenterPage } from '@/features/notifications/pages/NotificationCenterPage';
import { ReportsPage } from '@/features/reports/pages/ReportsPage';
import { SettingsPage } from '@/features/settings/pages/SettingsPage';
import { AuditLogsPage } from '@/features/audit/pages/AuditLogsPage';
import { ReachOutPage } from '@/features/reach_out/pages/ReachOutPage';
import { Student360PersonalPage } from '@/features/students/pages/Student360PersonalPage';
import { Student360AcademicPage } from '@/features/students/pages/Student360AcademicPage';
import { AcademicCorrectionsWorkspacePage } from '@/features/students/pages/AcademicCorrectionsWorkspacePage';


const router = createBrowserRouter([
  // Guest-only: an authenticated user is redirected out of these.
  {
    element: <GuestRoute />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
      { path: '/reset-password', element: <ResetPasswordPage /> },
    ],
  },

  // Standalone status pages — reachable regardless of auth state.
  { path: '/forbidden', element: <ForbiddenPage /> },
  { path: '/unauthorized', element: <UnauthorizedPage /> },
  { path: '/session-expired', element: <SessionExpiredPage /> },

  // Everything else requires a session.
  {
    element: <ProtectedRoute />,
    children: [
      // Reachable even while force_password_change is pending.
      { path: '/change-password', element: <ChangePasswordPage /> },

      // Everything below requires the temporary password to already be changed.
      {
        element: <RequirePasswordChange />,
        children: [
          {
            element: <AppLayout />,
            children: [
              // Shared, no extra guard beyond authentication.
              { path: '/', element: <Navigate to="/dashboard" replace /> },
              { path: '/dashboard', element: <DashboardPage /> },
              { path: '/reach-out', element: <ReachOutPage /> },
              { path: '/notifications', element: <NotificationCenterPage /> },
              { path: '/settings', element: <SettingsPage /> },

              // Student self-service portal — nested Student 360 Portal routes
              {
                element: <PermissionGuard permission="student.read" />,
                children: [
                  { path: '/my-workspace', element: <Navigate to="/student-360/personal" replace /> },
                  { path: '/student-360', element: <Navigate to="/student-360/personal" replace /> },
                  { path: '/student-360/personal', element: <Student360PersonalPage /> },
                  { path: '/student-360/academic', element: <Student360AcademicPage /> },
                  { path: '/student-360/corrections', element: <AcademicCorrectionsWorkspacePage /> },
                ],
              },

              {
                element: <PermissionGuard permission="profile.self.manage" />,
                children: [
                  { path: '/my-profile', element: <MyProfilePage /> },
                  { path: '/my-profile/:section', element: <MyProfilePage /> },
                ],
              },

              // Staff case-management. /students is the counsellor's primary
              // page (their assigned caseload); /students/:id is one student's
              // 360. Both are gated on student.read, and the backend
              // additionally scopes counsellors to assigned students — a
              // student holding student.read for their own record still gets
              // an empty caseload rather than the institution roster.
              {
                element: <PermissionGuard permission="student.caseload.read" />,
                children: [{ path: '/students', element: <MyStudentsPage /> }],
              },
              {
                element: <PermissionGuard permission="student.read" />,
                children: [{ path: '/students/:studentId', element: <StudentWorkspacePage /> }],
              },


              // Counselling — counsellor/HOD/admin.
              {
                element: <PermissionGuard permission="counselling.read" />,
                children: [{ path: '/counselling/sessions', element: <SessionsPage /> }],
              },
              {
                element: <PermissionGuard permission="counselling.create" />,
                children: [{ path: '/counselling/new', element: <NewSessionPage /> }],
              },

              // Attendance recording — faculty.
              {
                element: <PermissionGuard permission="attendance.create" />,
                children: [
                  { path: '/attendance', element: <RecordAttendancePage /> },
                  { path: '/attendance/record', element: <RecordAttendancePage /> },
                  { path: '/attendance/import', element: <AttendanceImportPage /> },
                ],
              },

              // Marks entry — faculty.
              {
                element: <PermissionGuard permission="marks.create" />,
                children: [
                  { path: '/academics', element: <MarksEntryPage /> },
                  { path: '/academics/marks', element: <MarksEntryPage /> },
                  { path: '/academics/import-marks', element: <MarksImportPage /> },
                ],
              },

              // Parent communication — counsellor/HOD/admin.
              {
                element: <PermissionGuard permission="parent_communication.read" />,
                children: [{ path: '/parent-communication', element: <ParentCommunicationPage /> }],
              },

              // Reports catalog — counsellor/HOD/admin. Gated on
              // report.generate (not report.download): students hold
              // report.download for their own history but must not reach the
              // institution-wide report generator.
              {
                element: <PermissionGuard permission="report.generate" />,
                children: [{ path: '/reports', element: <ReportsPage /> }],
              },

              // Admin-only, gated on the actual backend permission.
              {
                element: <PermissionGuard permission="user.manage" />,
                children: [
                  { path: '/admin/users', element: <UserManagementPage /> },
                  { path: '/admin/imports', element: <OfficeImportPage /> },
                  { path: '/admin/membership-import', element: <MembershipImportPage /> },
                  // The module used to live here as a CSV/UUID importer.
                  // Kept so bookmarks and older links still land somewhere.
                  { path: '/admin/bulk-import', element: <Navigate to="/admin/imports" replace /> },
                ],
              },
              {
                element: <PermissionGuard permission="department.manage" />,
                children: [
                  { path: '/admin/academic-config', element: <AcademicConfigPage /> },
                  { path: '/admin/assessment-config', element: <AssessmentConfigPage /> },
                ],
              },
              {
                element: <PermissionGuard permission="audit.read" />,
                children: [{ path: '/admin/audit-logs', element: <AuditLogsPage /> }],
              },
            ],
          },
        ],
      },
    ],
  },

  { path: '*', element: <Navigate to="/" replace /> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
