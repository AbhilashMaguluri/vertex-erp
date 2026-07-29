import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppHeader } from './AppHeader';
import { Sidebar } from './Sidebar';
import { UserRole } from '@scms/types';
import { Search, X, GraduationCap, User as UserIcon, Loader2 } from 'lucide-react';
import { searchService, SearchResultItem } from '@/features/search/search.service';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { cn } from '@/shared/utils/cn';

interface AppShellProps {
  children: React.ReactNode;
  userRole?: UserRole | string;
  userName?: string;
  onLogout?: () => void;
}

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

function GlobalSearch({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const [query, setQuery] = React.useState('');
  const debouncedQuery = useDebounced(query.trim(), 250);

  const { data: results, isFetching } = useQuery<SearchResultItem[]>({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchService.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const go = (item: SearchResultItem) => {
    onClose();
    navigate(item.url);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-20 backdrop-blur-sm animate-in fade-in-50 duration-150 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl rounded-2xl border border-border/80 bg-card p-0 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 border-b border-border/80 bg-muted/20">
          <Search className="h-4 w-4 text-muted-foreground shrink-0 mr-3" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search students and users..."
            className="w-full py-4 text-sm bg-transparent border-none focus:outline-none placeholder:text-muted-foreground/70"
          />
          {isFetching && <Loader2 className="h-4 w-4 text-muted-foreground animate-spin mr-2" />}
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto">
          {debouncedQuery.length < 2 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Type at least 2 characters to search.
            </div>
          ) : !results || results.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              {isFetching ? 'Searching…' : `No results for "${debouncedQuery}".`}
            </div>
          ) : (
            <div className="py-1.5">
              {results.map((item) => {
                const Icon = item.type === 'student' ? GraduationCap : UserIcon;
                return (
                  <button
                    key={`${item.type}-${item.id}`}
                    onClick={() => go(item)}
                    className={cn(
                      'flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-accent'
                    )}
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-bold text-foreground">{item.title}</p>
                      {item.subtitle && <p className="truncate text-[11px] text-muted-foreground">{item.subtitle}</p>}
                    </div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground/70">{item.type}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AppShell({
  children,
  userRole = UserRole.STUDENT,
  userName = 'User',
  onLogout,
}: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);
  const [isSearchOpen, setIsSearchOpen] = React.useState(false);

  // Global search is only offered to roles that can actually resolve results
  // (holders of student.read or user.manage). For a plain student the button
  // is hidden entirely rather than opening an always-empty palette.
  const canSearch = useSearchCapability();

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (canSearch && (e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
      if (e.key === 'Escape') setIsSearchOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canSearch]);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      <AppHeader
        onSearchClick={canSearch ? () => setIsSearchOpen(true) : undefined}
        userName={userName}
        userRole={userRole}
        onLogout={onLogout}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          role={userRole}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8">
          <div className="mx-auto max-w-7xl animate-in fade-in-50 duration-200">
            {children}
          </div>
        </main>
      </div>

      {isSearchOpen && canSearch && <GlobalSearch onClose={() => setIsSearchOpen(false)} />}
    </div>
  );
}

function useSearchCapability(): boolean {
  const { hasPermission } = useAuth();
  return hasPermission('student.read') || hasPermission('user.manage');
}
