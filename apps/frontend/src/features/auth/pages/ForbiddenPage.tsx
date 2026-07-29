import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';

export function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-radial from-background via-muted/30 to-background p-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-rose-500/10 text-rose-600 dark:text-rose-400 ring-8 ring-rose-500/5 mb-6 shadow-sm">
        <ShieldAlert className="h-10 w-10" />
      </div>

      <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
        403 — Access Restricted
      </h1>

      <p className="mt-2 max-w-md text-xs sm:text-sm text-muted-foreground leading-relaxed">
        Your account doesn't have permissions to view this specific section. If you believe your account role should have access, please contact your institutional administrator.
      </p>

      <div className="mt-8 flex items-center gap-3">
        <Button asChild size="lg" className="font-semibold">
          <Link to="/dashboard">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Safety (Dashboard)
          </Link>
        </Button>
      </div>
    </div>
  );
}
