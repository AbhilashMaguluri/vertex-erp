// ---------------------------------------------------------------------------
// usePageContext — Page awareness hook for Vertex
// ---------------------------------------------------------------------------
// Reads the current route and maps it to a PageContext object so Vertex
// knows *where* the user is in the ERP.
//
// Because Vertex mounts outside the Router (so it's available on every
// page), we can't use useLocation/useParams directly. Instead we listen
// to popstate + pushState to track the URL.
// ---------------------------------------------------------------------------

import { useMemo, useSyncExternalStore } from 'react';
import type { PageContext } from '../types/vertex';

// ---------------------------------------------------------------------------
// External store that tracks window.location.pathname
// ---------------------------------------------------------------------------

let _pathname = typeof window !== 'undefined' ? window.location.pathname : '/';
const _listeners = new Set<() => void>();

function notifyListeners() {
  _pathname = window.location.pathname;
  _listeners.forEach((fn) => fn());
}

// Patch pushState / replaceState so we detect SPA navigations
if (typeof window !== 'undefined') {
  const origPush = history.pushState.bind(history);
  const origReplace = history.replaceState.bind(history);

  history.pushState = function (...args) {
    origPush(...args);
    notifyListeners();
  };
  history.replaceState = function (...args) {
    origReplace(...args);
    notifyListeners();
  };

  window.addEventListener('popstate', notifyListeners);
}

function subscribe(cb: () => void) {
  _listeners.add(cb);
  return () => { _listeners.delete(cb); };
}

function getSnapshot() {
  return _pathname;
}

// ---------------------------------------------------------------------------
// Route → page mapping
// ---------------------------------------------------------------------------

function derivePage(pathname: string): string {
  if (pathname.startsWith('/students/') && pathname.split('/').length >= 3) return 'student-profile';
  if (pathname.startsWith('/counselling')) return 'counselling';
  if (pathname.startsWith('/attendance')) return 'attendance';
  if (pathname.startsWith('/academics')) return 'academics';
  if (pathname.startsWith('/reports')) return 'reports';
  if (pathname.startsWith('/reach-out')) return 'reach-out';
  if (pathname.startsWith('/parent-communication')) return 'parent-communication';
  if (pathname.startsWith('/notifications')) return 'notifications';
  if (pathname.startsWith('/settings')) return 'settings';
  if (pathname.startsWith('/my-workspace')) return 'my-workspace';
  if (pathname.startsWith('/my-profile')) return 'my-profile';
  if (pathname.startsWith('/admin/users')) return 'admin-users';
  if (pathname.startsWith('/admin/imports')) return 'admin-imports';
  if (pathname.startsWith('/admin/academic-config')) return 'admin-academic-config';
  if (pathname.startsWith('/admin/audit-logs')) return 'admin-audit-logs';
  if (pathname === '/dashboard' || pathname === '/') return 'dashboard';
  if (pathname === '/login') return 'login';
  if (pathname === '/forgot-password' || pathname === '/reset-password') return 'login';
  return 'unknown';
}

function extractStudentId(pathname: string): string | undefined {
  const match = pathname.match(/^\/students\/([^/]+)/);
  return match ? match[1] : undefined;
}

/** Human-readable label for the header status line */
export function pageDisplayName(page: string): string {
  const names: Record<string, string> = {
    'dashboard': 'Dashboard',
    'student-profile': 'Student Workspace',
    'counselling': 'Counselling',
    'attendance': 'Attendance',
    'academics': 'Academics',
    'reports': 'Reports',
    'reach-out': 'Reach Out Hub',
    'parent-communication': 'Parent Communication',
    'notifications': 'Notifications',
    'settings': 'Settings',
    'my-workspace': 'My Workspace',
    'my-profile': 'My Profile',
    'admin-users': 'User Management',
    'admin-imports': 'Data Imports',
    'admin-academic-config': 'Academic Config',
    'admin-audit-logs': 'Audit Logs',
    'login': 'Login',
    'unknown': 'VertexERP',
  };
  return names[page] || 'VertexERP';
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Tracks the current page context without requiring React Router context.
 * Uses useSyncExternalStore + patched history methods to detect SPA navs.
 */
export function usePageContext(): PageContext {
  const pathname = useSyncExternalStore(subscribe, getSnapshot);

  return useMemo<PageContext>(() => {
    const page = derivePage(pathname);
    const studentId = extractStudentId(pathname);
    return { page, studentId, params: {} };
  }, [pathname]);
}
