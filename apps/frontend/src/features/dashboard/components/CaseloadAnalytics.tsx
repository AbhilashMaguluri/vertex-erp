/**
 * Compact caseload analytics.
 *
 * Charting notes:
 *  - Every visualisation here is SINGLE-SERIES. Categories are named on the row
 *    or the axis, so identity never depends on colour and there is no
 *    categorical palette to keep colourblind-separable. The one series colour
 *    is --chart-series, a separately validated step per light/dark surface
 *    (see globals.css) — not one colour flipped between modes.
 *  - Risk is the exception and is deliberately status-coloured: the tier IS the
 *    meaning. Every row still carries its tier name and count as text, so the
 *    state is never conveyed by colour alone.
 *  - Distributions render as row meters rather than plotted bar charts. A
 *    counsellor reads "how many in each band", which a labelled row answers in
 *    a quarter of the height a full chart with axes would need.
 *  - Anything with no data is not rendered at all. An axis with nothing on it
 *    is worse than the space it occupies.
 */
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { CounsellorDashboard } from '@/features/counselling/services/counselling.service';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { yearLabel } from '@/features/students/components/StudentPresentation';
import { cn } from '@/shared/utils/cn';
import { BarChart3 } from 'lucide-react';

/** Status fills, used only where the colour genuinely means a severity tier.
 *  Never reused as a series colour. */
const RISK_FILL: Record<string, string> = {
  CRITICAL: 'bg-rose-600',
  HIGH: 'bg-rose-500',
  MEDIUM: 'bg-amber-500',
  LOW: 'bg-sky-500',
  NONE: 'bg-emerald-500',
};

const RISK_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE'];

interface MeterRow {
  label: string;
  value: number;
  /** Tailwind background class. Omitted rows use the single series colour. */
  fill?: string;
}

/** A labelled row meter: category name, a thin proportional bar, and the count.
 *  The count is always present as text, so the bar is an accelerant rather than
 *  the only way to read the value. */
function MeterList({ rows }: { rows: MeterRow[] }) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  return (
    <div className="space-y-2.5">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[minmax(0,7rem)_1fr_2.5rem] items-center gap-3">
          <span className="truncate text-[11px] font-semibold text-muted-foreground">{r.label}</span>
          <div className="h-2 overflow-hidden rounded-full bg-muted/60">
            <div
              className={cn('h-full rounded-full transition-all duration-500', r.fill)}
              style={{
                width: `${Math.max(2, (r.value / max) * 100)}%`,
                backgroundColor: r.fill ? undefined : 'var(--chart-series)',
              }}
            />
          </div>
          <span className="text-right text-xs font-bold tabular-nums text-foreground">{r.value}</span>
        </div>
      ))}
    </div>
  );
}

function AnalyticsCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">{title}</CardTitle>
        <CardDescription className="text-[11px]">{description}</CardDescription>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function CaseloadAnalytics({ data }: { data: CounsellorDashboard }) {
  const byYear: MeterRow[] = data.by_year
    .filter((b) => b.count > 0)
    .map((b) => ({
      label: b.bucket === 'Unassigned' ? 'Unassigned' : `${yearLabel(Number(b.bucket))} Year`,
      value: b.count,
    }));

  const byRisk: MeterRow[] = RISK_ORDER.map((level) => ({
    label: level,
    value: data.by_risk.find((b) => b.bucket === level)?.count ?? 0,
    fill: RISK_FILL[level],
  })).filter((r) => r.value > 0);

  const byAttendance: MeterRow[] = data.by_attendance_band
    .filter((b) => b.count > 0)
    .map((b) => ({ label: b.bucket, value: b.count }));

  const byType: MeterRow[] = data.sessions_by_type
    .filter((b) => b.count > 0)
    .map((b) => ({ label: b.bucket, value: b.count }));

  const hasTrend = data.sessions_by_month.length > 1;

  // Completion rate is one number, so it renders as a meter, not a chart.
  const followUpTotal = data.follow_ups_completed + data.follow_ups_pending;
  const completionRate =
    followUpTotal > 0 ? Math.round((data.follow_ups_completed / followUpTotal) * 100) : null;

  const panels = [
    byYear.length > 0 && (
      <AnalyticsCard
        key="year"
        title="Students by year"
        description="How your caseload spreads across study years"
      >
        <MeterList rows={byYear} />
      </AnalyticsCard>
    ),
    byRisk.length > 0 && (
      <AnalyticsCard key="risk" title="Risk distribution" description="Your caseload by current risk flag">
        <MeterList rows={byRisk} />
      </AnalyticsCard>
    ),
    byAttendance.length > 0 && (
      <AnalyticsCard
        key="attendance"
        title="Attendance distribution"
        description="Students with attendance on record, banded"
      >
        <MeterList rows={byAttendance} />
      </AnalyticsCard>
    ),
    byType.length > 0 && (
      <AnalyticsCard
        key="type"
        title="Sessions by category"
        description="What you are being consulted about"
      >
        <MeterList rows={byType} />
      </AnalyticsCard>
    ),
    completionRate !== null && (
      <AnalyticsCard
        key="completion"
        title="Follow-up completion"
        description={`${data.follow_ups_completed} closed of ${followUpTotal} raised`}
      >
        <div className="space-y-2">
          <div className="text-3xl font-black tracking-tight text-foreground">{completionRate}%</div>
          <div className="h-2 overflow-hidden rounded-full bg-muted/60">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${completionRate}%` }}
            />
          </div>
          <p className="text-[11px] text-muted-foreground">
            {data.follow_ups_overdue > 0
              ? `${data.follow_ups_overdue} of the open items are past their due date.`
              : 'No open item is past its due date.'}
          </p>
        </div>
      </AnalyticsCard>
    ),
    hasTrend && (
      <AnalyticsCard
        key="trend"
        title="Sessions over time"
        description="Counselling sessions you recorded, by month"
      >
        {/* Height covers plot + x-axis band, so the labels are never clipped
            into a nested scrollbar. */}
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={data.sessions_by_month} margin={{ top: 6, right: 10, bottom: 0, left: -24 }}>
            <CartesianGrid stroke="hsl(var(--chart-grid))" vertical={false} />
            <XAxis dataKey="bucket" tick={AXIS_TICK} tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={32} />
            <Tooltip content={<TrendTooltip />} cursor={{ stroke: 'hsl(var(--chart-grid))' }} />
            <Line
              type="monotone"
              dataKey="count"
              stroke="var(--chart-series)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--chart-series)', strokeWidth: 0 }}
              activeDot={{ r: 5, stroke: 'hsl(var(--card))', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </AnalyticsCard>
    ),
  ].filter(Boolean);

  // Every panel self-suppressed — there is genuinely nothing to plot yet.
  if (panels.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 p-8 text-center">
          <BarChart3 className="h-6 w-6 text-muted-foreground/50" />
          <p className="text-xs font-bold text-foreground">No analytics yet</p>
          <p className="max-w-md text-[11px] leading-relaxed text-muted-foreground">
            Caseload breakdowns appear once you have assigned students with attendance, marks or
            counselling history on record. Nothing is hidden — there is simply no data to chart.
          </p>
        </CardContent>
      </Card>
    );
  }

  return <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">{panels}</div>;
}

const AXIS_TICK = { fontSize: 10, fill: 'hsl(var(--chart-axis))', fontWeight: 600 };

function TrendTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-lg">
      <div className="text-[11px] font-bold text-popover-foreground">{label}</div>
      <div className="text-[11px] text-muted-foreground">
        {value} session{value === 1 ? '' : 's'}
      </div>
    </div>
  );
}
