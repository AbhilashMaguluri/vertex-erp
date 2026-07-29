import { Link } from 'react-router-dom';
import { LogIn, KeyRound } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-radial from-background via-muted/30 to-background p-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 text-primary ring-8 ring-primary/5 mb-6 shadow-sm">
        <KeyRound className="h-10 w-10" />
      </div>

      <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
        401 — Authentication Required
      </h1>

      <p className="mt-2 max-w-md text-xs sm:text-sm text-muted-foreground leading-relaxed">
        You must be signed in with valid institutional credentials to access this workspace resource.
      </p>

      <div className="mt-8">
        <Button asChild size="lg" className="font-semibold">
          <Link to="/login">
            <LogIn className="mr-2 h-4 w-4" />
            Proceed to Sign In
          </Link>
        </Button>
      </div>
    </div>
  );
}
