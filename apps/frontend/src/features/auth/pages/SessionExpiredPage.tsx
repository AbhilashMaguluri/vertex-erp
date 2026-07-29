import { Link } from 'react-router-dom';
import { TimerOff, LogIn } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';

export function SessionExpiredPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-radial from-background via-muted/30 to-background p-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-8 ring-amber-500/5 mb-6 shadow-sm">
        <TimerOff className="h-10 w-10" />
      </div>

      <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
        Session Expired
      </h1>

      <p className="mt-2 max-w-md text-xs sm:text-sm text-muted-foreground leading-relaxed">
        For your security, your session timed out after a period of inactivity. Sign in again to resume your work seamlessly.
      </p>

      <div className="mt-8">
        <Button asChild size="lg" className="font-semibold">
          <Link to="/login">
            <LogIn className="mr-2 h-4 w-4" />
            Sign In Again
          </Link>
        </Button>
      </div>
    </div>
  );
}
