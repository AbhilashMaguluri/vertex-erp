import * as React from 'react';
import { AppHeader } from './AppHeader';
import { Sidebar } from './Sidebar';
import { UserRole } from '@scms/types';

interface AppShellProps {
  children: React.ReactNode;
  userRole?: UserRole | string;
  userName?: string;
  onLogout?: () => void;
}

export function AppShell({
  children,
  userRole = UserRole.STUDENT,
  userName = 'User',
  onLogout,
}: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);
  const [isSearchOpen, setIsSearchOpen] = React.useState(false);

  // Global Ctrl+K / Cmd+K listener for Universal Search
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Top Header */}
      <AppHeader
        onSearchClick={() => setIsSearchOpen(true)}
        userName={userName}
        userRole={userRole}
        onLogout={onLogout}
      />

      {/* Body Area: Sidebar + Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          role={userRole}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>

      {/* Universal Search Command Palette Modal Stub */}
      {isSearchOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-20 backdrop-blur-xs animate-in fade-in-50"
          onClick={() => setIsSearchOpen(false)}
        >
          <div
            className="w-full max-w-xl rounded-lg border bg-card p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 border-b pb-3">
              <span className="text-sm font-medium">Universal Search (⌘K)</span>
              <span className="text-xs text-muted-foreground ml-auto">Esc to close</span>
            </div>
            <div className="py-8 text-center text-sm text-muted-foreground">
              Type to search across Students, Faculty, Sessions, Documents, and Reports...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
