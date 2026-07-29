/**
 * Building blocks for the student profile.
 *
 * `EditableSection` owns the view/edit lifecycle so every section behaves the
 * same way: read-only until you press Edit, explicit Save/Cancel, server
 * errors surfaced in place, and no silent discarding of typed input. Read-only
 * institution data uses `ReadOnlyField`, which is visually distinct so it is
 * obvious which values a student cannot change and why.
 */
import * as React from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Badge } from '@/shared/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { cn } from '@/shared/utils/cn';
import { Pencil, X, Check, Lock, Plus, AlertCircle } from 'lucide-react';

export function extractApiError(err: unknown, fallback = 'Something went wrong'): string {
  const e = err as {
    response?: { data?: { error?: { message?: string; details?: { field?: string; message: string }[] } } };
  };
  const envelope = e?.response?.data?.error;
  if (envelope?.details?.length) {
    // Field-level validation errors read better than the generic envelope
    // message ("Validation failed"), which tells the student nothing.
    return envelope.details.map((d) => (d.field ? `${d.field}: ${d.message}` : d.message)).join(' • ');
  }
  return envelope?.message ?? fallback;
}

interface EditableSectionProps {
  title: string;
  description?: string;
  /** Rendered when not editing. */
  children: React.ReactNode;
  /** Rendered while editing. */
  editContent: React.ReactNode;
  onSave: () => Promise<void> | void;
  onCancel?: () => void;
  isSaving?: boolean;
  error?: string | null;
  /** Hides the Edit button entirely — used for the counsellor's read-only view. */
  readOnly?: boolean;
  completion?: { completed: number; total: number };
}

export function EditableSection({
  title,
  description,
  children,
  editContent,
  onSave,
  onCancel,
  isSaving,
  error,
  readOnly,
  completion,
}: EditableSectionProps) {
  const [isEditing, setIsEditing] = React.useState(false);

  const handleCancel = () => {
    onCancel?.();
    setIsEditing(false);
  };

  const handleSave = async () => {
    await onSave();
    // Stays open when the save failed so typed input isn't thrown away —
    // the parent clears `error` on success and this effect closes the form.
  };

  // Close only once a save completes with no error.
  const prevSaving = React.useRef(false);
  React.useEffect(() => {
    if (prevSaving.current && !isSaving && !error) setIsEditing(false);
    prevSaving.current = !!isSaving;
  }, [isSaving, error]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            {title}
            {completion && completion.completed < completion.total && (
              <Badge variant="warning">
                {completion.completed}/{completion.total}
              </Badge>
            )}
            {completion && completion.completed === completion.total && (
              <Badge variant="success">Complete</Badge>
            )}
          </CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>

        {!readOnly && (
          <div className="flex shrink-0 items-center gap-2">
            {isEditing ? (
              <>
                <Button variant="outline" size="sm" onClick={handleCancel} disabled={isSaving}>
                  <X className="mr-1 h-3.5 w-3.5" /> Cancel
                </Button>
                <Button size="sm" onClick={handleSave} isLoading={isSaving}>
                  <Check className="mr-1 h-3.5 w-3.5" /> Save changes
                </Button>
              </>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                <Pencil className="mr-1 h-3.5 w-3.5" /> Edit
              </Button>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {error && isEditing && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs font-medium text-rose-600 dark:text-rose-400">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {isEditing ? editContent : children}
      </CardContent>
    </Card>
  );
}

/** A two-column responsive grid — the standard layout for profile forms. */
export function FieldGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{children}</div>;
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-muted-foreground/80">{hint}</p>}
    </div>
  );
}

/** Displays a saved value. "Not provided" is deliberate — an empty string
 *  would make a blank field look like a filled one. */
export function ValueField({ label, value }: { label: string; value?: string | number | null }) {
  const isEmpty = value === null || value === undefined || value === '';
  return (
    <div className="space-y-1">
      <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={cn('text-xs font-semibold', isEmpty ? 'text-muted-foreground/50 italic' : 'text-foreground')}>
        {isEmpty ? 'Not provided' : value}
      </div>
    </div>
  );
}

/** Institution-owned data. The lock icon and muted surface say "you cannot
 *  change this" without needing a disabled input that looks broken. */
export function ReadOnlyField({ label, value }: { label: string; value?: string | number | null }) {
  const isEmpty = value === null || value === undefined || value === '';
  return (
    <div className="space-y-1 rounded-xl border border-border/60 bg-muted/30 p-3">
      <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">
        <Lock className="h-2.5 w-2.5" />
        {label}
      </div>
      <div className={cn('text-xs font-bold', isEmpty ? 'text-muted-foreground/50 italic' : 'text-foreground')}>
        {isEmpty ? '—' : value}
      </div>
    </div>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <Input {...props} value={props.value ?? ''} />;
}

export function TextArea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      value={props.value ?? ''}
      className={cn(
        'w-full rounded-xl border border-input bg-background p-3 text-xs placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring',
        className
      )}
    />
  );
}

export function SelectInput({
  options,
  placeholder = 'Select…',
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  options: readonly string[] | { value: string; label: string }[];
  placeholder?: string;
}) {
  const normalised = options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o));
  return (
    <select
      {...props}
      value={props.value ?? ''}
      className="h-10 w-full rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring"
    >
      <option value="">{placeholder}</option>
      {normalised.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

/** Tag editor for the skill/language/interest lists. Enter or comma commits a
 *  tag; the backend de-duplicates too, so a race can't produce duplicates. */
export function TagInput({
  value,
  onChange,
  placeholder = 'Type and press Enter…',
}: {
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = React.useState('');

  const commit = (raw: string) => {
    const tag = raw.trim();
    if (!tag) return;
    if (value.some((v) => v.toLowerCase() === tag.toLowerCase())) {
      setDraft('');
      return;
    }
    onChange([...value, tag]);
    setDraft('');
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-[11px] font-bold text-primary"
          >
            {tag}
            <button
              type="button"
              onClick={() => onChange(value.filter((t) => t !== tag))}
              className="cursor-pointer text-primary/70 hover:text-primary"
              aria-label={`Remove ${tag}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {value.length === 0 && <span className="text-[11px] italic text-muted-foreground/60">None added yet</span>}
      </div>
      <div className="flex gap-2">
        <Input
          value={draft}
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ',') {
              e.preventDefault();
              commit(draft);
            }
            // Backspace on an empty box removes the last tag — standard
            // chip-input behaviour.
            if (e.key === 'Backspace' && !draft && value.length) {
              onChange(value.slice(0, -1));
            }
          }}
        />
        <Button type="button" variant="outline" size="sm" onClick={() => commit(draft)} disabled={!draft.trim()}>
          <Plus className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

export function TagList({ value }: { value?: string[] | null }) {
  if (!value?.length) {
    return <span className="text-xs italic text-muted-foreground/50">Not provided</span>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {value.map((tag) => (
        <Badge key={tag} variant="secondary">
          {tag}
        </Badge>
      ))}
    </div>
  );
}

/** Circular completion meter. Single hue, value stated as text — the ring is
 *  reinforcement, never the only carrier of the number. */
export function CompletionRing({ percentage, size = 96 }: { percentage: number; size?: number }) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, percentage)) / 100) * circumference;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          className="fill-none stroke-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ stroke: 'var(--chart-series)' }}
          className="fill-none transition-[stroke-dashoffset] duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-black tabular-nums text-foreground">{percentage}%</span>
        <span className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground">complete</span>
      </div>
    </div>
  );
}
