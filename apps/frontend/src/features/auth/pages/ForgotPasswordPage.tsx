import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import { forgotPasswordSchema, ForgotPasswordFormData } from '../schemas/auth.schema';
import { authService } from '../services/auth.service';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/shared/components/ui/Card';
import { Mail, ArrowLeft, CheckCircle2, KeyRound } from 'lucide-react';

export function ForgotPasswordPage() {
  const [isSubmitted, setIsSubmitted] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      setIsLoading(true);
      await authService.forgotPassword(data);
      setIsSubmitted(true);
    } catch (err) {
      // Always show success to prevent email enumeration (§26.3)
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-radial from-background via-muted/40 to-background px-4 py-12 relative overflow-hidden">
      <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-primary/10 blur-3xl pointer-events-none" />

      <Card className="w-full max-w-md shadow-xl border-border/80 bg-card/90 backdrop-blur-md relative z-10">
        <CardHeader className="space-y-2 text-center pb-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary font-bold text-xl shadow-xs ring-8 ring-primary/5 mb-2">
            <KeyRound className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-extrabold tracking-tight text-foreground">
            Reset Password
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Enter your institutional email address to receive password recovery instructions
          </CardDescription>
        </CardHeader>

        {isSubmitted ? (
          <CardContent className="space-y-5 pt-4 text-center pb-8">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 ring-8 ring-emerald-500/5">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <div className="space-y-1">
              <h4 className="text-base font-bold text-foreground">Check your inbox</h4>
              <p className="text-xs text-muted-foreground leading-relaxed max-w-xs mx-auto">
                If an account associated with that email exists, we have sent instructions to reset your password.
              </p>
            </div>
            <Button asChild variant="outline" size="lg" className="w-full">
              <Link to="/login">Return to Sign In</Link>
            </Button>
          </CardContent>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4 pt-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/70" />
                  <Input
                    {...register('email')}
                    type="email"
                    placeholder="student@college.edu"
                    className="pl-10"
                    disabled={isLoading}
                    error={!!errors.email}
                  />
                </div>
                {errors.email && (
                  <p className="text-[11px] text-destructive font-medium mt-1">{errors.email.message}</p>
                )}
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-4 pt-2 pb-6">
              <Button type="submit" size="lg" className="w-full font-semibold" isLoading={isLoading}>
                Send Recovery Instructions
              </Button>
              <Link
                to="/login"
                className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors font-medium"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Sign In
              </Link>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  );
}
