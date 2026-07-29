/**
 * Section 3 of the Student 360° Workspace — Counsellor Section.
 *
 * Read-only for the student, by construction: the API this reads has no
 * student-writable counterpart, so there is nothing here to edit even if the
 * UI offered it.
 *
 * What it deliberately does NOT show: a counsellor's confidential notes. The
 * counselling module strips them server-side for student callers and the
 * summary schema has no field for them at all.
 */
import { useQuery } from '@tanstack/react-query';
import {
  CalendarDays,
  ClipboardCheck,
  MessageSquare,
  PhoneCall,
  ShieldAlert,
  UserCheck,
} from 'lucide-react';
import { StudentCounsellingSummary, profileService } from '../services/profile.service';
import { CollapsibleCard, ReadOnlyBadge } from './ProfileWorkspaceKit';
import { RiskBadge, formatDate } from './StudentPresentation';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { cn } from '@/shared/utils/cn';

const RISK_GUIDANCE: Record<string, string> = {
  NONE: 'No concerns are currently flagged on your record.',
  LOW: 'A minor concern is being monitored by your counsellor.',
  MEDIUM: 'Your counsellor is actively following up on a concern.',
  HIGH: 'Your counsellor has flagged this as needing prompt attention.',
  CRITICAL: 'This is flagged as urgent. Please meet your counsellor as soon as you can.',
};

export function CounsellorSectionTab({ studentId }: { studentId?: string }) {
  const { data, isLoading, isError } = useQuery<StudentCounsellingSummary>({
    queryKey: ['students', studentId ?? 'me', 'counselling-summary'],
    queryFn: () =>
      studentId
        ? profileService.getStudentCounsellingSummary(studentId)
        : profileService.getMyCounsellingSummary(),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-24 rounded-3xl" />
        <Skeleton className="h-40 rounded-3xl" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="Could not load your counselling record"
        description="Please try again in a moment."
      />
    );
  }

  const pendingItems = data.action_items.filter((i) => i.status !== 'COMPLETED');

  return (
    <div className="space-y-3">
      <p className="flex items-center gap-2 rounded-2xl border border-border/60 bg-muted/20 px-4 py-2.5 text-[11px] font-medium text-muted-foreground">
        <ShieldAlert className="h-3.5 w-3.5 shrink-0 text-brand-600" />
        Written by your mentor and counsellor. You can read everything here, but only they can change it.
      </p>

      {/* Standing */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-3xl border border-border/80 bg-card p-4">
          <span className="mb-1 block text-[10px] font-black uppercase tracking-wider text-muted-foreground">
            Risk level
          </span>
          <RiskBadge level={data.risk_level} />
          <p className="mt-2 text-[11px] text-muted-foreground">
            {RISK_GUIDANCE[data.risk_level] ?? RISK_GUIDANCE.NONE}
          </p>
        </div>
        <div className="rounded-3xl border border-border/80 bg-card p-4">
          <span className="mb-1 block text-[10px] font-black uppercase tracking-wider text-muted-foreground">
            Counsellor
          </span>
          <p className="text-sm font-black text-foreground">{data.counsellor_name ?? 'Not assigned'}</p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            Mentor: {data.mentor_name ?? 'Not assigned'}
          </p>
        </div>
        <div className="rounded-3xl border border-border/80 bg-card p-4">
          <span className="mb-1 block text-[10px] font-black uppercase tracking-wider text-muted-foreground">
            Sessions
          </span>
          <p className="text-sm font-black text-foreground">{data.total_sessions}</p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            Last: {data.last_session_date ? formatDate(data.last_session_date) : 'None yet'}
          </p>
        </div>
        <div
          className={cn(
            'rounded-3xl border p-4',
            data.follow_up_required ? 'border-amber-500/40 bg-amber-500/5' : 'border-border/80 bg-card'
          )}
        >
          <span className="mb-1 block text-[10px] font-black uppercase tracking-wider text-muted-foreground">
            Follow-up required
          </span>
          <p className={cn('text-sm font-black', data.follow_up_required ? 'text-amber-600' : 'text-foreground')}>
            {data.follow_up_required ? 'Yes' : 'No'}
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            {pendingItems.length} open action item{pendingItems.length === 1 ? '' : 's'}
          </p>
        </div>
      </div>

      {/* Action items */}
      <CollapsibleCard
        id="action-items"
        title="Action Items"
        description="What you agreed to do, and by when"
        icon={ClipboardCheck}
        accent="amber"
        defaultOpen={pendingItems.length > 0}
        badge={<ReadOnlyBadge />}
      >
        {data.action_items.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">No action items have been set.</p>
        ) : (
          <ul className="space-y-2">
            {data.action_items.map((item) => (
              <li
                key={item.id}
                className={cn(
                  'flex flex-wrap items-center justify-between gap-2 rounded-xl border p-3',
                  item.is_overdue ? 'border-rose-500/30 bg-rose-500/5' : 'border-border/50 bg-muted/20'
                )}
              >
                <div className="min-w-0">
                  <p className="text-xs font-bold text-foreground">{item.description}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {item.due_date ? `Due ${formatDate(item.due_date)}` : 'No due date'}
                    {item.session_date ? ` • agreed on ${formatDate(item.session_date)}` : ''}
                  </p>
                </div>
                <span
                  className={cn(
                    'shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-extrabold',
                    item.status === 'COMPLETED'
                      ? 'bg-emerald-500/10 text-emerald-600'
                      : item.is_overdue
                        ? 'bg-rose-500/10 text-rose-600'
                        : 'bg-amber-500/10 text-amber-600'
                  )}
                >
                  {item.is_overdue && item.status !== 'COMPLETED' ? 'OVERDUE' : item.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleCard>

      {/* Remarks & progress notes */}
      <CollapsibleCard
        id="remarks"
        title="Mentor & Counsellor Remarks"
        description="Observations and recommendations from each session"
        icon={UserCheck}
        accent="brand"
        defaultOpen={data.notes.length > 0}
        badge={<ReadOnlyBadge />}
      >
        {data.notes.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">
            No counselling sessions have been recorded yet.
          </p>
        ) : (
          <div className="space-y-3">
            {data.notes.map((note) => (
              <article key={note.session_id} className="rounded-2xl border border-border/50 bg-muted/20 p-4">
                <header className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-brand-500/10 px-2.5 py-0.5 text-[10px] font-extrabold text-brand-600">
                    {note.session_type}
                  </span>
                  <span className="text-[11px] font-bold text-foreground">{formatDate(note.session_date)}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {note.counsellor_name ? `with ${note.counsellor_name}` : ''} • {note.mode.replace(/_/g, ' ')}
                  </span>
                  {note.student_acknowledged && (
                    <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-extrabold text-emerald-600">
                      Acknowledged
                    </span>
                  )}
                </header>

                <dl className="space-y-2 text-[11px]">
                  <div>
                    <dt className="font-black uppercase tracking-wider text-muted-foreground">Observations</dt>
                    <dd className="whitespace-pre-wrap font-medium text-foreground">{note.observations}</dd>
                  </div>
                  {note.recommendations && (
                    <div>
                      <dt className="font-black uppercase tracking-wider text-muted-foreground">Recommendations</dt>
                      <dd className="whitespace-pre-wrap font-medium text-foreground">{note.recommendations}</dd>
                    </div>
                  )}
                  {note.student_commitments && (
                    <div>
                      <dt className="font-black uppercase tracking-wider text-muted-foreground">
                        What you committed to
                      </dt>
                      <dd className="whitespace-pre-wrap font-medium text-foreground">{note.student_commitments}</dd>
                    </div>
                  )}
                </dl>

                {note.follow_up_required && (
                  <p className="mt-2 text-[11px] font-bold text-amber-600">
                    Follow-up {note.follow_up_date ? `scheduled for ${formatDate(note.follow_up_date)}` : 'required'}
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
      </CollapsibleCard>

      {/* Parent interaction notes */}
      <CollapsibleCard
        id="parent-notes"
        title="Parent Interaction Notes"
        description="Conversations the college has had with your family"
        icon={PhoneCall}
        accent="indigo"
        badge={<ReadOnlyBadge />}
      >
        {data.parent_interactions.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">
            No parent conversations have been recorded.
          </p>
        ) : (
          <div className="space-y-2">
            {data.parent_interactions.map((entry) => (
              <article key={entry.id} className="rounded-2xl border border-border/50 bg-muted/20 p-3">
                <header className="mb-1 flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="font-bold text-foreground">{formatDate(entry.communication_date)}</span>
                  <span className="text-muted-foreground">
                    {entry.parent_name} ({entry.relation}) • {entry.mode.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-[10px] font-extrabold',
                      entry.outcome === 'POSITIVE'
                        ? 'bg-emerald-500/10 text-emerald-600'
                        : entry.outcome === 'CONCERNING'
                          ? 'bg-rose-500/10 text-rose-600'
                          : 'bg-muted text-muted-foreground'
                    )}
                  >
                    {entry.outcome}
                  </span>
                </header>
                <p className="whitespace-pre-wrap text-[11px] font-medium text-foreground">{entry.summary}</p>
                {entry.action_items && (
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    <span className="font-black uppercase tracking-wider">Actions:</span> {entry.action_items}
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
      </CollapsibleCard>

      {/* Timeline */}
      <CollapsibleCard
        id="timeline"
        title="Counselling History Timeline"
        description="Every recorded interaction, newest first"
        icon={CalendarDays}
        accent="purple"
        badge={<ReadOnlyBadge />}
      >
        {data.notes.length === 0 && data.parent_interactions.length === 0 ? (
          <p className="text-[11px] italic text-muted-foreground/60">Nothing recorded yet.</p>
        ) : (
          <ol className="relative space-y-4 border-l border-border/60 pl-5">
            {[
              ...data.notes.map((n) => ({
                key: `s-${n.session_id}`,
                date: n.session_date,
                title: `${n.session_type} session`,
                detail: n.counsellor_name ? `with ${n.counsellor_name}` : 'Counselling session',
                tone: 'brand' as const,
              })),
              ...data.parent_interactions.map((p) => ({
                key: `p-${p.id}`,
                date: p.communication_date,
                title: `Parent contact — ${p.relation}`,
                detail: `${p.parent_name} • ${p.outcome}`,
                tone: 'indigo' as const,
              })),
            ]
              .sort((a, b) => (a.date < b.date ? 1 : -1))
              .map((event) => (
                <li key={event.key} className="relative">
                  <span
                    className={cn(
                      'absolute -left-[27px] top-1 h-3 w-3 rounded-full ring-4 ring-card',
                      event.tone === 'brand' ? 'bg-brand-500' : 'bg-indigo-500'
                    )}
                  />
                  <p className="text-[11px] font-bold text-foreground">{event.title}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {formatDate(event.date)} • {event.detail}
                  </p>
                </li>
              ))}
          </ol>
        )}
      </CollapsibleCard>
    </div>
  );
}
