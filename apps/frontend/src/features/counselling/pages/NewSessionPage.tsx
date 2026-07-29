import * as React from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { counsellingService, SessionCreateData } from '../services/counselling.service';
import { studentService } from '@/features/students/services/student.service';
import {
  AttendanceCell,
  GpaCell,
  RiskBadge,
  StudentAvatar,
  formatDate,
  formatSessionDate,
  yearLabel,
} from '@/features/students/components/StudentPresentation';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/shared/components/ui/Card';
import {
  AlertCircle,
  Plus,
  Trash2,
  ArrowLeft,
  ShieldCheck,
  Search,
  Users,
  Lock,
  History,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';

const MIN_OBSERVATION_CHARS = 50;

/** Form values only — student_id is NOT part of the form. It comes from the
 *  selected student's record, so there is no field a counsellor could mistype
 *  and no id a client could substitute. */
type SessionFormValues = Omit<SessionCreateData, 'student_id'>;

export function NewSessionPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const studentId = searchParams.get('studentId') || searchParams.get('student_id') || '';
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const { data: context, isLoading: contextLoading, isError: contextError } = useQuery({
    queryKey: ['students', studentId, 'session-context'],
    queryFn: () => studentService.getSessionContext(studentId),
    enabled: !!studentId,
  });

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SessionFormValues>({
    defaultValues: {
      session_date: new Date().toISOString().split('T')[0],
      session_type: 'ACADEMIC',
      mode: 'IN_PERSON',
      observations: '',
      recommendations: '',
      student_commitments: '',
      confidential_notes: '',
      follow_up_required: false,
      risk_assessment: 'NONE',
      confidential: false,
      action_items: [],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'action_items' });

  const followUpRequired = watch('follow_up_required');
  const observationsValue = watch('observations') || '';

  const onSubmit = async (values: SessionFormValues) => {
    if (!studentId) {
      setErrorMsg('Select a student before saving the session.');
      return;
    }
    try {
      setErrorMsg(null);
      setIsSubmitting(true);
      await counsellingService.createSession({ ...values, student_id: studentId });
      // The caseload's "last session" column and the student's counselling
      // history are both now stale.
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['counselling'] });
      navigate(`/students/${studentId}?tab=counselling`);
    } catch (err) {
      const message =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ??
        'Failed to record session';
      setErrorMsg(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // No student chosen yet — pick one from the caseload instead of typing an id.
  if (!studentId) {
    return (
      <>
        <Breadcrumbs
          items={[
            { label: 'Counselling Sessions', href: '/counselling/sessions' },
            { label: 'Record New Session' },
          ]}
        />
        <PageHeader
          title="Record Counselling Session"
          subtitle="Choose the student you met with — their record loads automatically"
        />
        <StudentPicker onSelect={(id) => setSearchParams({ studentId: id })} />
      </>
    );
  }

  if (contextLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-40 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (contextError || !context) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Could not load this student"
        description="They may not be assigned to you, or the record no longer exists. Pick another student from your caseload."
        actionLabel="Back to Assigned Students"
        onAction={() => navigate('/students')}
      />
    );
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Counselling Sessions', href: '/counselling/sessions' },
          { label: context.full_name, href: `/students/${context.student_id}` },
          { label: 'New Session' },
        ]}
      />

      <PageHeader
        title="Record Counselling Session"
        subtitle="Student details are loaded from their record — review the context, then log the interaction"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setSearchParams({})}>
              Change student
            </Button>
            <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
              <ArrowLeft className="mr-1.5 h-4 w-4" /> Cancel
            </Button>
          </div>
        }
      />

      {/* Auto-populated student context — replaces the old Student ID field */}
      <Card className="mt-6">
        <CardContent className="p-5 md:p-6">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
            <div className="flex items-center gap-4">
              <StudentAvatar name={context.full_name} size="lg" />
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-xl font-black tracking-tight text-foreground">{context.full_name}</h2>
                  <RiskBadge level={context.risk_level} />
                </div>
                <div className="font-mono text-[11px] text-muted-foreground">{context.roll_number}</div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                  {context.department_name && <span>{context.department_name}</span>}
                  {context.section_name && <span>• Section {context.section_name}</span>}
                  {context.study_year && <span>• {yearLabel(context.study_year)} Year</span>}
                  {context.semester_name && <span>• Sem {context.semester_name}</span>}
                </div>
              </div>
            </div>

            <Link to={`/students/${context.student_id}`}>
              <Button variant="outline" size="sm">
                <ExternalLink className="mr-1.5 h-3.5 w-3.5" /> Full record
              </Button>
            </Link>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3 border-t border-border/70 pt-5 lg:grid-cols-4">
            <ContextTile label="Attendance">
              <AttendanceCell value={context.attendance_percentage} />
            </ContextTile>
            <ContextTile label="CGPA">
              <GpaCell value={context.cgpa} />
            </ContextTile>
            <ContextTile label="Active backlogs">
              {context.active_backlogs > 0 ? (
                <Badge variant="warning">{context.active_backlogs}</Badge>
              ) : (
                <span className="font-bold text-foreground">None</span>
              )}
            </ContextTile>
            <ContextTile label="Sessions to date">
              <span className="font-bold tabular-nums text-foreground">{context.total_sessions}</span>
              <span className="ml-1.5 text-[11px] text-muted-foreground">
                last {formatSessionDate(context.last_session_date)}
              </span>
            </ContextTile>
          </div>

          {context.attention_items.length > 0 && (
            <div className="mt-4 space-y-2 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3.5">
              {context.attention_items.map((item, i) => (
                <div key={i} className="flex items-start gap-2 text-xs font-medium text-amber-800 dark:text-amber-300">
                  <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Previous session + outstanding commitments */}
      {(context.last_session_summary || context.pending_action_items.length > 0) && (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {context.last_session_summary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <History className="h-4 w-4 text-primary" />
                  Previous session
                </CardTitle>
                <CardDescription>
                  {context.last_session_type} • {formatDate(context.last_session_date)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs leading-relaxed text-muted-foreground">{context.last_session_summary}</p>
              </CardContent>
            </Card>
          )}

          {context.pending_action_items.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  Outstanding action items
                </CardTitle>
                <CardDescription>Agreed in earlier sessions and not yet completed</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {context.pending_action_items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start justify-between gap-3 rounded-xl border border-border/70 bg-muted/20 p-3"
                  >
                    <span className="text-xs font-medium text-foreground">{item.description}</span>
                    <Badge variant={item.is_overdue ? 'destructive' : 'secondary'} className="shrink-0">
                      {item.is_overdue ? 'Overdue' : 'Due'} {formatDate(item.due_date)}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-6">
        {errorMsg && (
          <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs font-medium text-rose-600 dark:text-rose-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Session parameters</CardTitle>
            <CardDescription>How, when and in what capacity you met</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Session date">
              <Input type="date" {...register('session_date', { required: true })} />
            </Field>

            <Field label="Category / focus">
              <Select {...register('session_type')}>
                <option value="ACADEMIC">ACADEMIC — Performance &amp; attendance</option>
                <option value="PERSONAL">PERSONAL — Well-being &amp; guidance</option>
                <option value="BEHAVIOURAL">BEHAVIOURAL — Conduct &amp; discipline</option>
                <option value="CAREER">CAREER — Guidance &amp; placement</option>
                <option value="HEALTH">HEALTH — Medical concerns</option>
                <option value="FINANCIAL">FINANCIAL — Fees &amp; assistance</option>
              </Select>
            </Field>

            <Field label="Interaction mode">
              <Select {...register('mode')}>
                <option value="IN_PERSON">IN PERSON — Face to face</option>
                <option value="PHONE">PHONE — Telephonic</option>
                <option value="VIDEO_CALL">VIDEO CALL — Remote</option>
              </Select>
            </Field>

            <Field label="Risk assessment">
              <Select {...register('risk_assessment')}>
                <option value="NONE">NONE — No concern</option>
                <option value="LOW">LOW — Monitor</option>
                <option value="MEDIUM">MEDIUM — Elevated concern</option>
                <option value="HIGH">HIGH — Priority intervention</option>
                <option value="CRITICAL">CRITICAL — Immediate action</option>
              </Select>
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="text-base">Observations &amp; guidance</CardTitle>
              <CardDescription>What you observed, what you advised, and what the student agreed to</CardDescription>
            </div>
            <span
              className={`shrink-0 font-mono text-xs font-bold ${
                observationsValue.length < MIN_OBSERVATION_CHARS ? 'text-amber-600' : 'text-emerald-600'
              }`}
            >
              {observationsValue.length} / {MIN_OBSERVATION_CHARS} min
            </span>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Observations" required>
              <Textarea
                rows={5}
                placeholder="What the student described, how they presented, context from their record…"
                {...register('observations', {
                  required: 'Observations are required',
                  minLength: {
                    value: MIN_OBSERVATION_CHARS,
                    message: `Minimum ${MIN_OBSERVATION_CHARS} characters required`,
                  },
                })}
              />
              {errors.observations && (
                <p className="text-[11px] font-medium text-destructive">{errors.observations.message}</p>
              )}
            </Field>

            <Field label="Recommendations">
              <Textarea
                rows={3}
                placeholder="Guidance offered — remedial classes, referrals, study plan, resources…"
                {...register('recommendations')}
              />
            </Field>

            <Field label="Student commitments">
              <Textarea
                rows={3}
                placeholder="What the student agreed to do before the next meeting…"
                {...register('student_commitments')}
              />
            </Field>
          </CardContent>
        </Card>

        {/* Confidential notes — visually separated because of who can read it */}
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Lock className="h-4 w-4 text-amber-600" />
              Confidential notes
            </CardTitle>
            <CardDescription>
              Visible to counsellors and administrators only. The student never sees this, on any screen or export.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              rows={3}
              placeholder="Sensitive context that should not be shared with the student…"
              {...register('confidential_notes')}
            />
            <label className="flex cursor-pointer select-none items-center gap-2 text-xs font-semibold text-foreground">
              <input type="checkbox" {...register('confidential')} className="h-4 w-4 rounded border-input" />
              Also mark the entire session as confidential
            </label>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base">Action items &amp; follow-up</CardTitle>
              <CardDescription>Specific, dated tasks you can check on next time</CardDescription>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ description: '', due_date: new Date().toISOString().split('T')[0] })}
            >
              <Plus className="mr-1 h-3.5 w-3.5" /> Add item
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {fields.length === 0 && (
              <p className="text-xs text-muted-foreground">No action items yet — add one if the student committed to something specific.</p>
            )}
            {fields.map((field, index) => (
              <div key={field.id} className="flex items-center gap-2">
                <Input
                  {...register(`action_items.${index}.description` as const, { required: true })}
                  placeholder="Task description…"
                  className="flex-1"
                />
                <Input
                  type="date"
                  {...register(`action_items.${index}.due_date` as const, { required: true })}
                  className="w-44"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => remove(index)}
                  className="text-destructive hover:bg-rose-500/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}

            <div className="flex flex-wrap items-center gap-6 border-t border-border/80 pt-4">
              <label className="flex cursor-pointer select-none items-center gap-2 text-xs font-semibold text-foreground">
                <input type="checkbox" {...register('follow_up_required')} className="h-4 w-4 rounded border-input" />
                Schedule a follow-up session
              </label>

              {followUpRequired && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Follow-up date:</span>
                  <Input type="date" {...register('follow_up_date')} className="w-44" />
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex items-center justify-between border-t border-border/80 pt-4">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-primary" />
              <span>Recorded against {context.roll_number} — audited and immutable</span>
            </div>
            <div className="flex items-center gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" isLoading={isSubmitting}>
                Save session
              </Button>
            </div>
          </CardFooter>
        </Card>
      </form>
    </>
  );
}

function ContextTile({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border/60 bg-muted/30 p-3">
      <div className="text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="mt-1.5 flex items-center text-sm">{children}</div>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-semibold text-foreground">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </label>
      {children}
    </div>
  );
}

const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  (props, ref) => (
    <select
      ref={ref}
      className="h-10 w-full rounded-lg border border-input bg-background px-3 text-xs font-medium focus:ring-2 focus:ring-ring"
      {...props}
    />
  )
);
Select.displayName = 'Select';

const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={`w-full rounded-xl border border-input bg-background p-3.5 text-xs placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring ${className ?? ''}`}
      {...props}
    />
  )
);
Textarea.displayName = 'Textarea';

/** Searchable caseload picker. The counsellor selects a person, never an id. */
function StudentPicker({ onSelect }: { onSelect: (studentId: string) => void }) {
  const [search, setSearch] = React.useState('');
  const [debounced, setDebounced] = React.useState('');

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const { data, isLoading } = useQuery({
    queryKey: ['students', 'caseload', 'picker', debounced],
    queryFn: () => studentService.getCaseload({ search: debounced || undefined, per_page: 12 }),
    placeholderData: keepPreviousData,
  });

  const students = data?.data ?? [];

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="text-base">Select a student</CardTitle>
        <CardDescription>Search your assigned students by name or roll number</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            autoFocus
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Start typing a name or roll number…"
            className="pl-9"
          />
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : students.length === 0 ? (
          <EmptyState
            icon={Users}
            title={debounced ? 'No matching students' : 'No students assigned'}
            description={
              debounced
                ? 'No student in your caseload matches that search.'
                : 'An administrator assigns students to counsellors. Once you have a caseload it appears here.'
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {students.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelect(s.id)}
                className="flex cursor-pointer items-center gap-3 rounded-xl border border-border/70 bg-card p-3 text-left transition-all hover:border-primary/50 hover:bg-accent"
              >
                <StudentAvatar name={s.full_name} photoUrl={s.photo_url} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-xs font-bold text-foreground">{s.full_name}</div>
                  <div className="truncate font-mono text-[11px] text-muted-foreground">
                    {s.roll_number}
                    {s.section_name ? ` • Sec ${s.section_name}` : ''}
                  </div>
                </div>
                <RiskBadge level={s.risk_level} />
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
