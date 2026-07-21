import { Bell, LogOut } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';

interface AppHeaderProps {
  userName?: string;
  userRole?: string;
  onLogout?: () => void;
  onSearchClick?: () => void;
}

export function AppHeader({ userName = 'User', userRole = 'STUDENT', onLogout }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur-xs">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-semibold text-foreground">
          Student Counselling Management System (SCMS)
        </h2>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground">
          <Bell className="h-4 w-4" />
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-destructive" />
        </Button>

        <div className="h-4 w-px bg-border" />

        <div className="flex items-center gap-2">
          <div className="flex flex-col text-right">
            <span className="text-xs font-medium text-foreground">{userName}</span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{userRole}</span>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            title="Sign out"
            className="text-muted-foreground hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
