import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/shared/utils/cn';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold transition-all focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 select-none shrink-0 tracking-tight',
  {
    variants: {
      variant: {
        default:
          'border border-primary/20 bg-primary/10 text-primary hover:bg-primary/20',
        secondary:
          'border border-border/80 bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive:
          'border border-rose-500/20 bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20',
        outline:
          'border border-border text-foreground hover:bg-accent',
        success:
          'border border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20',
        warning:
          'border border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20',
        info:
          'border border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-300 hover:bg-sky-500/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

function Badge({ className, variant, dot = false, children, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props}>
      {dot && (
        <span
          className={cn(
            'h-1.5 w-1.5 rounded-full animate-pulse',
            variant === 'success' && 'bg-emerald-500',
            variant === 'warning' && 'bg-amber-500',
            variant === 'destructive' && 'bg-rose-500',
            variant === 'info' && 'bg-sky-500',
            (!variant || variant === 'default') && 'bg-primary'
          )}
        />
      )}
      {children}
    </div>
  );
}

export { Badge, badgeVariants };
