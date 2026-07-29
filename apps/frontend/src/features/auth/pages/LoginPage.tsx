import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { loginSchema, LoginFormData } from '../schemas/auth.schema';
import { useAuth } from '../hooks/useAuth';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { AlertCircle, Eye, EyeOff, Lock, UserRound, ShieldCheck, GraduationCap, Calendar } from 'lucide-react';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [generalError, setGeneralError] = React.useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);

  const deactivated = searchParams.get('deactivated') === 'true';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { rememberMe: false },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setGeneralError(null);
      setIsLoggingIn(true);
      const user = await login(data);
      const from = (location.state as { from?: Location })?.from?.pathname;
      if (user.force_password_change) {
        navigate('/change-password', { replace: true });
      } else {
        navigate(from || '/dashboard', { replace: true });
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        'Those credentials were not recognised. Check your roll number or email and password.';
      setGeneralError(msg);
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full bg-background antialiased overflow-hidden">
      {/* Left Panel — Campus Photography + Brand Showcase (Hidden on Mobile) */}
      <div className="hidden lg:flex lg:w-7/12 relative text-white p-12 flex-col justify-between overflow-hidden">
        {/* Real VVIT campus photography */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url('/vvit-campus.jpg')" }}
          role="img"
          aria-label="Aerial view of the VVIT campus"
        />
        {/* Scrim — keeps overlaid text at AA contrast against the photo */}
        <div className="absolute inset-0 bg-gradient-to-br from-navy-950/96 via-navy-900/92 to-navy-950/97" />
        {/* Brand glow accents */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 h-96 w-96 rounded-full bg-brand-500/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 h-80 w-80 rounded-full bg-navy-400/20 blur-3xl pointer-events-none" />

        {/* Top Header Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="flex items-center justify-center rounded-xl bg-white p-1.5 shadow-lg shadow-black/20">
            <img src="/vvit-logo.png" alt="VVIT University" className="h-9 w-auto object-contain" />
          </div>
          <div>
            <h2 className="text-base font-black tracking-tight text-white">VVIT Counselling Portal</h2>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest">Student Counselling & Academic System</p>
          </div>
        </div>

        {/* Middle Feature Cards Grid */}
        <div className="relative z-10 my-auto space-y-6 max-w-xl">
          <div className="space-y-3">
            <Badge variant="outline" className="text-brand-200 border-brand-300/30 bg-brand-500/15">
              Vasireddy Venkatadri Institute of Technology
            </Badge>
            <h1 className="text-4xl font-black tracking-tight text-white leading-tight">
              A Unified Home for Student Counselling & Academic Care
            </h1>
            <p className="text-sm text-slate-300/90 leading-relaxed">
              Attendance, marks, and counselling sessions — tracked in one place for faculty, counsellors, and administrators.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2 backdrop-blur-md">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500/15 text-brand-200">
                <GraduationCap className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-bold text-white">360° Student Workspace</h4>
              <p className="text-[11px] text-slate-300/80 leading-relaxed">Academic history, GPA trends, and early risk signals in one view.</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2 backdrop-blur-md">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-300">
                <Calendar className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-bold text-white">Attendance & Marks</h4>
              <p className="text-[11px] text-slate-300/80 leading-relaxed">Faculty log entries with instant defaulter tracking.</p>
            </div>
          </div>
        </div>

        {/* Bottom Footer */}
        <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-6 text-xs text-slate-400 font-medium">
          <span>© 2026 Vasireddy Venkatadri Institute of Technology</span>
          <span className="flex items-center gap-1.5 text-slate-300"><ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Secure institutional access</span>
        </div>
      </div>

      {/* Right Panel — Auth Form Card */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative bg-card overflow-hidden">
        {/* Subtle brand-tinted glow for depth, echoing the left panel */}
        <div className="absolute top-0 right-0 -mr-32 -mt-32 h-96 w-96 rounded-full bg-brand-500/[0.06] blur-3xl pointer-events-none" />

        <div className="w-full max-w-sm space-y-8 relative z-10">
          <div className="space-y-2 text-center lg:text-left">
            <div className="lg:hidden mx-auto w-fit mb-4 flex items-center rounded-2xl bg-white px-3 py-2 ring-1 ring-border shadow-sm">
              <img src="/vvit-logo.png" alt="VVIT University" className="h-9 w-auto object-contain" />
            </div>
            <span className="hidden lg:inline-block text-[11px] font-extrabold text-brand-600 uppercase tracking-widest">
              Welcome back
            </span>
            <h2 className="text-2xl font-black tracking-tight text-foreground">Sign in to your workspace</h2>
            <p className="text-xs text-muted-foreground">
              Enter your institutional credentials to continue
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {deactivated && (
              <div className="flex items-center gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3.5 text-xs font-medium text-amber-700 dark:text-amber-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>This account has been deactivated. Contact administrator.</span>
              </div>
            )}
            {generalError && (
              <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs font-medium text-rose-600 dark:text-rose-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{generalError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Roll Number or Institutional Email</label>
              <div className="relative">
                <UserRound className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/70" />
                {/* type="text", not "email": students sign in with the roll
                    number on their credential slip, which the browser would
                    otherwise reject as malformed. */}
                <Input
                  {...register('email')}
                  type="text"
                  placeholder="23BQ1A5401  or  you@vvitguntur.com"
                  className="pl-10"
                  disabled={isLoggingIn}
                  error={!!errors.email}
                  autoComplete="username"
                  autoCapitalize="none"
                  spellCheck={false}
                />
              </div>
              {errors.email && (
                <p className="text-[11px] text-rose-500 font-medium mt-1">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-foreground">Password</label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-primary hover:underline underline-offset-2"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/70" />
                <Input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="pl-10 pr-10"
                  disabled={isLoggingIn}
                  error={!!errors.password}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-3 text-muted-foreground/70 hover:text-foreground p-0.5 rounded-sm"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-[11px] text-rose-500 font-medium mt-1">{errors.password.message}</p>
              )}
            </div>

            <label className="flex items-center gap-2 text-xs text-muted-foreground select-none cursor-pointer pt-1">
              <input type="checkbox" className="h-4 w-4 rounded border-input text-primary focus:ring-ring" {...register('rememberMe')} />
              Keep me signed in on this device
            </label>

            <Button type="submit" size="lg" className="w-full font-bold mt-2" isLoading={isLoggingIn}>
              Sign In to Workspace
            </Button>
          </form>

          <p className="text-center text-[11px] text-muted-foreground leading-relaxed">
            Institutional credentials are managed by the VVIT Counselling Portal administrator.
          </p>
        </div>
      </div>
    </div>
  );
}
