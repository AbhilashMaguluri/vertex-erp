import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';
import { Card, CardContent } from './Card';
import { cn } from '@/shared/utils/cn';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  icon?: LucideIcon;
  progress?: number;
  className?: string;
}

export function StatCard({
  title,
  value,
  change,
  trend = 'neutral',
  description,
  icon: Icon,
  progress,
  className,
}: StatCardProps) {
  return (
    <Card className={cn('relative overflow-hidden group hover:border-primary/50 transition-all duration-200', className)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-extrabold text-muted-foreground uppercase tracking-widest">
            {title}
          </span>
          {Icon && (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20 group-hover:scale-110 transition-transform duration-200">
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline justify-between gap-2">
          <span className="text-3xl font-black tracking-tight text-foreground">
            {value}
          </span>

          {change && (
            <div
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold select-none',
                trend === 'up' && 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20',
                trend === 'down' && 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20',
                trend === 'neutral' && 'bg-secondary text-muted-foreground border border-border/60'
              )}
            >
              {trend === 'up' && <TrendingUp className="h-3 w-3" />}
              {trend === 'down' && <TrendingDown className="h-3 w-3" />}
              {trend === 'neutral' && <Minus className="h-3 w-3" />}
              <span>{change}</span>
            </div>
          )}
        </div>

        {progress !== undefined && (
          <div className="mt-3 space-y-1">
            <div className="h-1.5 w-full rounded-full bg-muted/60 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-400 to-brand-600 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          </div>
        )}

        {description && (
          <p className="mt-2 text-[11px] text-muted-foreground/80 leading-relaxed font-medium">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
