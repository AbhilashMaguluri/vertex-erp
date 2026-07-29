/**
 * The student's professional record: internships, interview history,
 * achievements and documents.
 *
 * All four share a shape — list, add via modal, edit, delete — so they share
 * `CollectionShell`. Each accepts `readOnly` for the counsellor's Student 360
 * view, where the same data renders without any mutation control.
 */
import * as React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  profileService,
  Achievement,
  Internship,
  Interview,
  StudentDocument,
  ACHIEVEMENT_CATEGORIES,
  DOCUMENT_TYPES,
  INTERNSHIP_STATUSES,
  INTERVIEW_RESULTS,
  INTERVIEW_TYPES,
} from '../services/profile.service';
import { Button } from '@/shared/components/ui/Button';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { Field, FieldGrid, SelectInput, TagInput, TextArea, TextInput, extractApiError } from './ProfileForm';
import { formatDate } from './StudentPresentation';
import {
  Briefcase,
  Building2,
  Plus,
  Pencil,
  Trash2,
  Trophy,
  FileText,
  Upload,
  Download,
  AlertCircle,
  X,
  MessageSquare,
} from 'lucide-react';

const humanise = (v: string) => v.replace(/_/g, ' ');

// --------------------------------------------------------------------------
// Shared shell
// --------------------------------------------------------------------------

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
      <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto border-border bg-card shadow-2xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-border/70 bg-card px-5 py-4">
          <h3 className="text-base font-bold text-foreground">{title}</h3>
          <button onClick={onClose} className="cursor-pointer text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <CardContent className="space-y-4 p-5">{children}</CardContent>
      </Card>
    </div>
  );
}

function ErrorBanner({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs font-medium text-rose-600 dark:text-rose-400">
      <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

function CollectionShell({
  title,
  description,
  isLoading,
  isEmpty,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  onAdd,
  addLabel,
  readOnly,
  children,
}: {
  title: string;
  description: string;
  isLoading: boolean;
  isEmpty: boolean;
  emptyIcon: any;
  emptyTitle: string;
  emptyDescription: string;
  onAdd?: () => void;
  addLabel: string;
  readOnly?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-foreground">{title}</h2>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
        {!readOnly && onAdd && (
          <Button size="sm" onClick={onAdd}>
            <Plus className="mr-1.5 h-3.5 w-3.5" /> {addLabel}
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
        </div>
      ) : isEmpty ? (
        <EmptyState
          icon={emptyIcon}
          title={emptyTitle}
          description={emptyDescription}
          actionLabel={!readOnly && onAdd ? addLabel : undefined}
          onAction={!readOnly ? onAdd : undefined}
        />
      ) : (
        children
      )}
    </div>
  );
}

function RowActions({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  const [confirming, setConfirming] = React.useState(false);
  if (confirming) {
    return (
      <div className="flex shrink-0 items-center gap-1.5">
        <span className="text-[11px] font-semibold text-muted-foreground">Delete?</span>
        <Button size="sm" variant="destructive" onClick={onDelete}>
          Yes
        </Button>
        <Button size="sm" variant="outline" onClick={() => setConfirming(false)}>
          No
        </Button>
      </div>
    );
  }
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <Button size="sm" variant="ghost" onClick={onEdit} aria-label="Edit">
        <Pencil className="h-3.5 w-3.5" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={() => setConfirming(true)}
        className="text-destructive hover:bg-rose-500/10"
        aria-label="Delete"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

// --------------------------------------------------------------------------
// Internships
// --------------------------------------------------------------------------

export function InternshipsTab({ studentId, readOnly }: { studentId?: string; readOnly?: boolean }) {
  const qc = useQueryClient();
  const [editing, setEditing] = React.useState<Internship | null>(null);
  const [isCreating, setIsCreating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const queryKey = readOnly ? ['students', studentId, 'internships'] : ['profile', 'internships'];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      readOnly ? profileService.listStudentInternships(studentId!) : profileService.listInternships(),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey });
    qc.invalidateQueries({ queryKey: ['profile'] });
  };

  const saveMutation = useMutation({
    mutationFn: (vars: { id?: string; payload: Record<string, unknown> }) =>
      vars.id
        ? profileService.updateInternship(vars.id, vars.payload)
        : profileService.createInternship(vars.payload),
    onSuccess: () => {
      invalidate();
      setEditing(null);
      setIsCreating(false);
      setError(null);
    },
    onError: (e) => setError(extractApiError(e, 'Could not save the internship')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileService.deleteInternship(id),
    onSuccess: invalidate,
    onError: (e) => setError(extractApiError(e, 'Could not delete the internship')),
  });

  const items = data ?? [];

  return (
    <>
      <ErrorBanner message={error} />
      <CollectionShell
        title="Internships"
        description="Industry experience you have completed or are currently doing"
        isLoading={isLoading}
        isEmpty={items.length === 0}
        emptyIcon={Briefcase}
        emptyTitle="No internships added"
        emptyDescription={
          readOnly
            ? 'This student has not recorded any internships yet.'
            : 'Add internships so your counsellor can see your industry experience.'
        }
        onAdd={() => {
          setError(null);
          setIsCreating(true);
        }}
        addLabel="Add internship"
        readOnly={readOnly}
      >
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-start justify-between gap-4 p-4">
                <div className="min-w-0 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-bold text-foreground">{item.role}</span>
                    <span className="text-xs text-muted-foreground">at {item.company}</span>
                    <Badge variant={item.status === 'ONGOING' ? 'info' : 'secondary'}>
                      {humanise(item.status)}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {item.start_date ? formatDate(item.start_date) : '—'} –{' '}
                    {item.end_date ? formatDate(item.end_date) : 'Present'}
                    {item.duration ? ` • ${item.duration}` : ''}
                    {item.stipend ? ` • ₹${item.stipend}/month` : ''}
                  </div>
                  {item.technologies?.length ? (
                    <div className="flex flex-wrap gap-1">
                      {item.technologies.map((t) => (
                        <Badge key={t} variant="outline">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                  {item.description && (
                    <p className="text-xs leading-relaxed text-muted-foreground">{item.description}</p>
                  )}
                </div>
                {!readOnly && (
                  <RowActions
                    onEdit={() => {
                      setError(null);
                      setEditing(item);
                    }}
                    onDelete={() => deleteMutation.mutate(item.id)}
                  />
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CollectionShell>

      {(isCreating || editing) && (
        <InternshipModal
          initial={editing}
          isSaving={saveMutation.isPending}
          error={error}
          onClose={() => {
            setEditing(null);
            setIsCreating(false);
            setError(null);
          }}
          onSubmit={(payload) => saveMutation.mutate({ id: editing?.id, payload })}
        />
      )}
    </>
  );
}

function InternshipModal({
  initial,
  onClose,
  onSubmit,
  isSaving,
  error,
}: {
  initial: Internship | null;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => void;
  isSaving: boolean;
  error: string | null;
}) {
  const [form, setForm] = React.useState({
    company: initial?.company ?? '',
    role: initial?.role ?? '',
    start_date: initial?.start_date ?? '',
    end_date: initial?.end_date ?? '',
    duration: initial?.duration ?? '',
    stipend: initial?.stipend != null ? String(initial.stipend) : '',
    description: initial?.description ?? '',
    status: initial?.status ?? 'COMPLETED',
  });
  const [technologies, setTechnologies] = React.useState<string[]>(initial?.technologies ?? []);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <Modal title={initial ? 'Edit internship' : 'Add internship'} onClose={onClose}>
      <ErrorBanner message={error} />
      <FieldGrid>
        <Field label="Company *">
          <TextInput value={form.company} onChange={(e) => set('company', e.target.value)} />
        </Field>
        <Field label="Role *">
          <TextInput value={form.role} onChange={(e) => set('role', e.target.value)} />
        </Field>
        <Field label="Start date">
          <TextInput type="date" value={form.start_date} onChange={(e) => set('start_date', e.target.value)} />
        </Field>
        <Field label="End date">
          <TextInput type="date" value={form.end_date} onChange={(e) => set('end_date', e.target.value)} />
        </Field>
        <Field label="Duration" hint="e.g. 8 weeks">
          <TextInput value={form.duration} onChange={(e) => set('duration', e.target.value)} />
        </Field>
        <Field label="Stipend (₹ per month)">
          <TextInput type="number" min={0} value={form.stipend} onChange={(e) => set('stipend', e.target.value)} />
        </Field>
        <Field label="Status">
          <SelectInput
            options={INTERNSHIP_STATUSES.map((s) => ({ value: s, label: humanise(s) }))}
            value={form.status}
            onChange={(e) => set('status', e.target.value)}
            placeholder="Select status"
          />
        </Field>
      </FieldGrid>

      <Field label="Technologies used">
        <TagInput value={technologies} onChange={setTechnologies} placeholder="React, Node.js…" />
      </Field>

      <Field label="What you worked on">
        <TextArea rows={3} value={form.description} onChange={(e) => set('description', e.target.value)} />
      </Field>

      <div className="flex justify-end gap-2 border-t border-border/70 pt-3">
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
        <Button
          size="sm"
          isLoading={isSaving}
          disabled={!form.company.trim() || !form.role.trim()}
          onClick={() =>
            onSubmit({
              ...form,
              stipend: form.stipend ? Number(form.stipend) : null,
              start_date: form.start_date || null,
              end_date: form.end_date || null,
              technologies,
            })
          }
        >
          {initial ? 'Save changes' : 'Add internship'}
        </Button>
      </div>
    </Modal>
  );
}

// --------------------------------------------------------------------------
// Interviews
// --------------------------------------------------------------------------

function resultVariant(result: string) {
  if (result === 'SELECTED') return 'success' as const;
  if (result === 'REJECTED') return 'destructive' as const;
  if (result === 'ON_HOLD') return 'warning' as const;
  return 'secondary' as const;
}

export function InterviewsTab({
  studentId,
  readOnly,
  canObserve,
}: {
  studentId?: string;
  readOnly?: boolean;
  /** Counsellor-only: adds coaching feedback to an interview. */
  canObserve?: boolean;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = React.useState<Interview | null>(null);
  const [isCreating, setIsCreating] = React.useState(false);
  const [observing, setObserving] = React.useState<Interview | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const queryKey = readOnly ? ['students', studentId, 'interviews'] : ['profile', 'interviews'];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      readOnly ? profileService.listStudentInterviews(studentId!) : profileService.listInterviews(),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey });
    qc.invalidateQueries({ queryKey: ['profile'] });
  };

  const saveMutation = useMutation({
    mutationFn: (vars: { id?: string; payload: Record<string, unknown> }) =>
      vars.id
        ? profileService.updateInterview(vars.id, vars.payload)
        : profileService.createInterview(vars.payload),
    onSuccess: () => {
      invalidate();
      setEditing(null);
      setIsCreating(false);
      setError(null);
    },
    onError: (e) => setError(extractApiError(e, 'Could not save the interview')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileService.deleteInterview(id),
    onSuccess: invalidate,
    onError: (e) => setError(extractApiError(e, 'Could not delete the interview')),
  });

  const observeMutation = useMutation({
    mutationFn: (vars: { id: string; observation: string }) =>
      profileService.setInterviewObservation(studentId!, vars.id, vars.observation),
    onSuccess: () => {
      invalidate();
      setObserving(null);
      setError(null);
    },
    onError: (e) => setError(extractApiError(e, 'Could not save the observation')),
  });

  const items = data ?? [];

  return (
    <>
      <ErrorBanner message={error} />
      <CollectionShell
        title="Interview history"
        description="Companies you have interviewed with and how each went"
        isLoading={isLoading}
        isEmpty={items.length === 0}
        emptyIcon={Building2}
        emptyTitle="No interviews recorded"
        emptyDescription={
          readOnly
            ? 'This student has not recorded any interviews yet.'
            : 'Track every interview so you and your counsellor can spot patterns.'
        }
        onAdd={() => {
          setError(null);
          setIsCreating(true);
        }}
        addLabel="Add interview"
        readOnly={readOnly}
      >
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-foreground">{item.company}</span>
                      <span className="text-xs text-muted-foreground">— {item.role}</span>
                      <Badge variant={resultVariant(item.result)}>{humanise(item.result)}</Badge>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {item.interview_date ? formatDate(item.interview_date) : 'Date not set'}
                      {item.interview_type ? ` • ${humanise(item.interview_type)}` : ''}
                      {item.round_name ? ` • ${item.round_name}` : ''}
                      {item.package_offered ? ` • ₹${item.package_offered} LPA` : ''}
                    </div>
                    {item.feedback && (
                      <p className="text-xs leading-relaxed text-muted-foreground">
                        <span className="font-bold text-foreground">Feedback: </span>
                        {item.feedback}
                      </p>
                    )}
                    {item.notes && (
                      <p className="text-xs leading-relaxed text-muted-foreground">
                        <span className="font-bold text-foreground">Notes: </span>
                        {item.notes}
                      </p>
                    )}
                  </div>
                  {!readOnly && (
                    <RowActions
                      onEdit={() => {
                        setError(null);
                        setEditing(item);
                      }}
                      onDelete={() => deleteMutation.mutate(item.id)}
                    />
                  )}
                </div>

                {item.counsellor_observation && (
                  <div className="rounded-xl border border-primary/20 bg-primary/5 p-3">
                    <div className="mb-1 flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest text-primary">
                      <MessageSquare className="h-3 w-3" /> Counsellor observation
                      {item.counsellor_observed_by_name ? ` — ${item.counsellor_observed_by_name}` : ''}
                    </div>
                    <p className="text-xs leading-relaxed text-foreground">{item.counsellor_observation}</p>
                  </div>
                )}

                {canObserve && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setError(null);
                      setObserving(item);
                    }}
                  >
                    <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                    {item.counsellor_observation ? 'Update observation' : 'Add observation'}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CollectionShell>

      {(isCreating || editing) && (
        <InterviewModal
          initial={editing}
          isSaving={saveMutation.isPending}
          error={error}
          onClose={() => {
            setEditing(null);
            setIsCreating(false);
            setError(null);
          }}
          onSubmit={(payload) => saveMutation.mutate({ id: editing?.id, payload })}
        />
      )}

      {observing && (
        <ObservationModal
          interview={observing}
          isSaving={observeMutation.isPending}
          error={error}
          onClose={() => setObserving(null)}
          onSubmit={(observation) => observeMutation.mutate({ id: observing.id, observation })}
        />
      )}
    </>
  );
}

function InterviewModal({
  initial,
  onClose,
  onSubmit,
  isSaving,
  error,
}: {
  initial: Interview | null;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => void;
  isSaving: boolean;
  error: string | null;
}) {
  const [form, setForm] = React.useState({
    company: initial?.company ?? '',
    role: initial?.role ?? '',
    interview_date: initial?.interview_date ?? '',
    interview_type: initial?.interview_type ?? '',
    round_name: initial?.round_name ?? '',
    result: initial?.result ?? 'PENDING',
    feedback: initial?.feedback ?? '',
    notes: initial?.notes ?? '',
    package_offered: initial?.package_offered != null ? String(initial.package_offered) : '',
  });
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <Modal title={initial ? 'Edit interview' : 'Add interview'} onClose={onClose}>
      <ErrorBanner message={error} />
      <FieldGrid>
        <Field label="Company *">
          <TextInput value={form.company} onChange={(e) => set('company', e.target.value)} />
        </Field>
        <Field label="Role *">
          <TextInput value={form.role} onChange={(e) => set('role', e.target.value)} />
        </Field>
        <Field label="Interview date">
          <TextInput
            type="date"
            value={form.interview_date}
            onChange={(e) => set('interview_date', e.target.value)}
          />
        </Field>
        <Field label="Type">
          <SelectInput
            options={INTERVIEW_TYPES.map((t) => ({ value: t, label: humanise(t) }))}
            value={form.interview_type}
            onChange={(e) => set('interview_type', e.target.value)}
            placeholder="Select type"
          />
        </Field>
        <Field label="Round" hint="e.g. Technical Round 2">
          <TextInput value={form.round_name} onChange={(e) => set('round_name', e.target.value)} />
        </Field>
        <Field label="Result">
          <SelectInput
            options={INTERVIEW_RESULTS.map((r) => ({ value: r, label: humanise(r) }))}
            value={form.result}
            onChange={(e) => set('result', e.target.value)}
            placeholder="Select result"
          />
        </Field>
        <Field label="Package offered (₹ LPA)">
          <TextInput
            type="number"
            min={0}
            value={form.package_offered}
            onChange={(e) => set('package_offered', e.target.value)}
          />
        </Field>
      </FieldGrid>

      <Field label="Interview feedback" hint="What the panel said">
        <TextArea rows={3} value={form.feedback} onChange={(e) => set('feedback', e.target.value)} />
      </Field>
      <Field label="Your notes" hint="What you would do differently">
        <TextArea rows={3} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
      </Field>

      <div className="flex justify-end gap-2 border-t border-border/70 pt-3">
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
        <Button
          size="sm"
          isLoading={isSaving}
          disabled={!form.company.trim() || !form.role.trim()}
          onClick={() =>
            onSubmit({
              ...form,
              interview_date: form.interview_date || null,
              package_offered: form.package_offered ? Number(form.package_offered) : null,
            })
          }
        >
          {initial ? 'Save changes' : 'Add interview'}
        </Button>
      </div>
    </Modal>
  );
}

function ObservationModal({
  interview,
  onClose,
  onSubmit,
  isSaving,
  error,
}: {
  interview: Interview;
  onClose: () => void;
  onSubmit: (observation: string) => void;
  isSaving: boolean;
  error: string | null;
}) {
  const [text, setText] = React.useState(interview.counsellor_observation ?? '');
  return (
    <Modal title={`Observation — ${interview.company}`} onClose={onClose}>
      <ErrorBanner message={error} />
      <p className="text-xs text-muted-foreground">
        Coaching feedback on this interview. The student can read this — it is not a confidential
        counselling note.
      </p>
      <TextArea
        rows={5}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What went well, what to work on before the next round…"
      />
      <div className="flex justify-end gap-2 border-t border-border/70 pt-3">
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
        <Button size="sm" isLoading={isSaving} disabled={!text.trim()} onClick={() => onSubmit(text)}>
          Save observation
        </Button>
      </div>
    </Modal>
  );
}

// --------------------------------------------------------------------------
// Achievements
// --------------------------------------------------------------------------

export function AchievementsTab({ studentId, readOnly }: { studentId?: string; readOnly?: boolean }) {
  const qc = useQueryClient();
  const [editing, setEditing] = React.useState<Achievement | null>(null);
  const [isCreating, setIsCreating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const queryKey = readOnly ? ['students', studentId, 'achievements'] : ['profile', 'achievements'];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      readOnly ? profileService.listStudentAchievements(studentId!) : profileService.listAchievements(),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey });
    qc.invalidateQueries({ queryKey: ['profile'] });
  };

  const saveMutation = useMutation({
    mutationFn: (vars: { id?: string; payload: Record<string, unknown> }) =>
      vars.id
        ? profileService.updateAchievement(vars.id, vars.payload)
        : profileService.createAchievement(vars.payload),
    onSuccess: () => {
      invalidate();
      setEditing(null);
      setIsCreating(false);
      setError(null);
    },
    onError: (e) => setError(extractApiError(e, 'Could not save the achievement')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileService.deleteAchievement(id),
    onSuccess: invalidate,
    onError: (e) => setError(extractApiError(e, 'Could not delete the achievement')),
  });

  const items = data ?? [];

  return (
    <>
      <ErrorBanner message={error} />
      <CollectionShell
        title="Achievements"
        description="Hackathons, certifications, competitions, sports, clubs and volunteering"
        isLoading={isLoading}
        isEmpty={items.length === 0}
        emptyIcon={Trophy}
        emptyTitle="No achievements added"
        emptyDescription={
          readOnly
            ? 'This student has not recorded any achievements yet.'
            : 'Record what you have won, published or organised — it strengthens your profile.'
        }
        onAdd={() => {
          setError(null);
          setIsCreating(true);
        }}
        addLabel="Add achievement"
        readOnly={readOnly}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-start justify-between gap-3 p-4">
                <div className="min-w-0 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-bold text-foreground">{item.title}</span>
                    <Badge variant="outline">{humanise(item.category)}</Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {item.issuer ? `${item.issuer} • ` : ''}
                    {item.achieved_on ? formatDate(item.achieved_on) : 'Date not set'}
                    {item.position ? ` • ${item.position}` : ''}
                  </div>
                  {item.description && (
                    <p className="text-xs leading-relaxed text-muted-foreground">{item.description}</p>
                  )}
                  {item.credential_url && (
                    <a
                      href={item.credential_url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="text-[11px] font-bold text-primary hover:underline"
                    >
                      View credential
                    </a>
                  )}
                </div>
                {!readOnly && (
                  <RowActions
                    onEdit={() => {
                      setError(null);
                      setEditing(item);
                    }}
                    onDelete={() => deleteMutation.mutate(item.id)}
                  />
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CollectionShell>

      {(isCreating || editing) && (
        <AchievementModal
          initial={editing}
          isSaving={saveMutation.isPending}
          error={error}
          onClose={() => {
            setEditing(null);
            setIsCreating(false);
            setError(null);
          }}
          onSubmit={(payload) => saveMutation.mutate({ id: editing?.id, payload })}
        />
      )}
    </>
  );
}

function AchievementModal({
  initial,
  onClose,
  onSubmit,
  isSaving,
  error,
}: {
  initial: Achievement | null;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => void;
  isSaving: boolean;
  error: string | null;
}) {
  const [form, setForm] = React.useState({
    title: initial?.title ?? '',
    category: initial?.category ?? 'OTHER',
    issuer: initial?.issuer ?? '',
    achieved_on: initial?.achieved_on ?? '',
    position: initial?.position ?? '',
    credential_url: initial?.credential_url ?? '',
    description: initial?.description ?? '',
  });
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <Modal title={initial ? 'Edit achievement' : 'Add achievement'} onClose={onClose}>
      <ErrorBanner message={error} />
      <FieldGrid>
        <Field label="Title *">
          <TextInput value={form.title} onChange={(e) => set('title', e.target.value)} />
        </Field>
        <Field label="Category">
          <SelectInput
            options={ACHIEVEMENT_CATEGORIES.map((c) => ({ value: c, label: humanise(c) }))}
            value={form.category}
            onChange={(e) => set('category', e.target.value)}
            placeholder="Select category"
          />
        </Field>
        <Field label="Issued / organised by">
          <TextInput value={form.issuer} onChange={(e) => set('issuer', e.target.value)} />
        </Field>
        <Field label="Date">
          <TextInput type="date" value={form.achieved_on} onChange={(e) => set('achieved_on', e.target.value)} />
        </Field>
        <Field label="Position / rank" hint="e.g. Winner, Runner-up">
          <TextInput value={form.position} onChange={(e) => set('position', e.target.value)} />
        </Field>
        <Field label="Credential URL">
          <TextInput
            value={form.credential_url}
            placeholder="https://…"
            onChange={(e) => set('credential_url', e.target.value)}
          />
        </Field>
      </FieldGrid>
      <Field label="Description">
        <TextArea rows={3} value={form.description} onChange={(e) => set('description', e.target.value)} />
      </Field>

      <div className="flex justify-end gap-2 border-t border-border/70 pt-3">
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
        <Button
          size="sm"
          isLoading={isSaving}
          disabled={!form.title.trim()}
          onClick={() => onSubmit({ ...form, achieved_on: form.achieved_on || null })}
        >
          {initial ? 'Save changes' : 'Add achievement'}
        </Button>
      </div>
    </Modal>
  );
}

// --------------------------------------------------------------------------
// Documents
// --------------------------------------------------------------------------

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentsTab({ studentId, readOnly }: { studentId?: string; readOnly?: boolean }) {
  const qc = useQueryClient();
  const [error, setError] = React.useState<string | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [docType, setDocType] = React.useState('RESUME');
  const fileRef = React.useRef<HTMLInputElement>(null);

  const queryKey = readOnly ? ['students', studentId, 'documents'] : ['profile', 'documents'];
  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      readOnly ? profileService.listStudentDocuments(studentId!) : profileService.listDocuments(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => profileService.deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey }),
    onError: (e) => setError(extractApiError(e, 'Could not delete the document')),
  });

  const handleUpload = async (file: File) => {
    setError(null);
    setIsUploading(true);
    try {
      await profileService.uploadDocument(file, docType);
      qc.invalidateQueries({ queryKey });
      qc.invalidateQueries({ queryKey: ['profile'] });
    } catch (e) {
      setError(extractApiError(e, 'Upload failed'));
    } finally {
      setIsUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const items = data ?? [];

  return (
    <div className="space-y-4">
      <ErrorBanner message={error} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-foreground">Documents</h2>
          <p className="text-xs text-muted-foreground">
            {readOnly
              ? 'Documents this student has uploaded. Read-only.'
              : 'PDF, JPG, PNG, WEBP, DOC or DOCX — up to 10MB each.'}
          </p>
        </div>

        {!readOnly && (
          <div className="flex items-center gap-2">
            <SelectInput
              options={DOCUMENT_TYPES.map((d) => ({ value: d.value, label: d.label }))}
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              placeholder="Type"
            />
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(file);
              }}
            />
            <Button size="sm" isLoading={isUploading} onClick={() => fileRef.current?.click()}>
              <Upload className="mr-1.5 h-3.5 w-3.5" /> Upload
            </Button>
          </div>
        )}
      </div>

      {isLoading ? (
        <Skeleton className="h-32 w-full rounded-xl" />
      ) : items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents uploaded"
          description={
            readOnly
              ? 'This student has not uploaded any documents yet.'
              : 'Upload your resume, certificates and ID documents so they are all in one place.'
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {items.map((doc: StudentDocument) => (
            <Card key={doc.id}>
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-xs font-bold text-foreground">
                      {doc.title || doc.original_filename}
                    </div>
                    <div className="truncate text-[11px] text-muted-foreground">
                      {humanise(doc.document_type)} • {formatBytes(doc.size_bytes)} •{' '}
                      {formatDate(doc.created_at)}
                    </div>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <Button
                    size="sm"
                    variant="ghost"
                    aria-label="Download"
                    onClick={() =>
                      profileService
                        .downloadDocument(doc.student_id, doc.id, doc.original_filename, doc.file_url)
                        .catch((e) => setError(extractApiError(e, 'Download failed')))
                    }
                  >
                    <Download className="h-3.5 w-3.5" />
                  </Button>
                  {!readOnly && (
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label="Delete"
                      className="text-destructive hover:bg-rose-500/10"
                      onClick={() => deleteMutation.mutate(doc.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
