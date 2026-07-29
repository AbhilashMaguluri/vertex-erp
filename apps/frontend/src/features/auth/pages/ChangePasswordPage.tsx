import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { changePasswordSchema, ChangePasswordFormData } from '../schemas/auth.schema';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/auth.service';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/shared/components/ui/Card';
import { AlertCircle, Lock, ShieldCheck } from 'lucide-react';

export function ChangePasswordPage() {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const isForced = !!user?.force_password_change;

  const [generalError, setGeneralError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = async (data: ChangePasswordFormData) => {
    try {
      setGeneralError(null);
      setIsSubmitting(true);
      await authService.changePassword(data);
      await refreshUser();
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setGeneralError(err?.response?.data?.error?.message || 'Could not change your password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4 py-12">
      <Card className="w-full max-w-md shadow-lg border-border">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-2">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <CardTitle className="text-xl font-bold tracking-tight">
            {isForced ? 'Set a New Password' : 'Change Password'}
          </CardTitle>
          <CardDescription>
            {isForced
              ? 'Your account was created with a temporary password. Choose a new one to continue.'
              : 'Update the password used to sign in to your account.'}
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4 pt-4">
            {generalError && (
              <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs font-medium text-rose-600 dark:text-rose-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{generalError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">
                {isForced ? 'Temporary Password' : 'Current Password'}
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  {...register('currentPassword')}
                  type="password"
                  className="pl-9"
                  disabled={isSubmitting}
                  autoComplete="current-password"
                />
              </div>
              {errors.currentPassword && (
                <p className="text-[11px] text-destructive font-medium">{errors.currentPassword.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  {...register('newPassword')}
                  type="password"
                  className="pl-9"
                  disabled={isSubmitting}
                  autoComplete="new-password"
                />
              </div>
              {errors.newPassword && (
                <p className="text-[11px] text-destructive font-medium">{errors.newPassword.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Confirm New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  {...register('confirmPassword')}
                  type="password"
                  className="pl-9"
                  disabled={isSubmitting}
                  autoComplete="new-password"
                />
              </div>
              {errors.confirmPassword && (
                <p className="text-[11px] text-destructive font-medium">{errors.confirmPassword.message}</p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3 pt-2">
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Updating...' : 'Update Password'}
            </Button>
            {isForced ? (
              <button
                type="button"
                onClick={() => logout()}
                className="text-center text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Sign out instead
              </button>
            ) : (
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="text-center text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
            )}
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
