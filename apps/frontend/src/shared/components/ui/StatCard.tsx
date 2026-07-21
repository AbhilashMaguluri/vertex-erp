import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent } from './Card';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
}

export function StatCard({ title, value, change, trend = 'neutral', description }: StatCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-6">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</span>

        <div className="mt-2 flex items-baseline justify-between">
          <span className="text-2xl font-bold tracking-tight text-foreground">{value}</span>

          {change && (
            <div
              className={`flex items-center text-xs font-semibold ${
                trend === 'up'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : trend === 'down'
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-muted-foreground'
              }`}
            >
              {trend === 'up' && <TrendingUp className="mr-1 h-3.5 w-3.5" />}
              {trend === 'down' && <TrendingDown className="mr-1 h-3.5 w-3.5" />}
              {trend === 'neutral' && <Minus className="mr-1 h-3.5 w-3.5" />}
              <span>{change}</span>
            </div>
          )}
        </div>

        {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  );
}
