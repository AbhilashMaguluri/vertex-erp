/**
 * Primitives for the Student 360° Workspace.
 *
 * ProfileForm.tsx supplies the explicit Edit → Save → Cancel section used by
 * the counsellor's view. This file supplies what the *student's* workspace
 * needs on top of it:
 *
 *   • CollapsibleCard   — progressive disclosure, so the profile is a set of
 *                         cards rather than one wall of inputs.
 *   • useSectionAutosave — debounced per-section PATCH with a visible status,
 *                         so a student never loses typed input by navigating
 *                         away without pressing a button.
 *   • MultiSelectChips  — closed-vocabulary pickers (support areas,
 *                         extracurriculars) where free text would break the
 *                         counsellor's filters.
 *   • PhotoUploadDialog — client-side square crop before upload; the server
 *                         never receives the untrimmed original.
 *   • AuthedImage       — profile photos are served from an authenticated
 *                         route, so an <img src> would 401. This fetches the
 *                         bytes with the API client and renders a blob URL.
 */
import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  Check,
  ChevronDown,
  Loader2,
  Lock,
  RotateCcw,
  Upload,
  X,
  ZoomIn,
} from 'lucide-react';
import { api } from '@/shared/lib/axios';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { cn } from '@/shared/utils/cn';
import { extractApiError } from './ProfileForm';

// ---------------------------------------------------------------------------
// Collapsible card
// ---------------------------------------------------------------------------

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

export function SaveIndicator({ status, error }: { status: SaveStatus; error?: string | null }) {
  if (status === 'saving') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" /> Saving…
      </span>
    );
  }
  if (status === 'saved') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600">
        <Check className="h-3 w-3" /> Saved
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-600" title={error ?? undefined}>
        <AlertCircle className="h-3 w-3" /> Not saved
      </span>
    );
  }
  return null;
}

export function CollapsibleCard({
  id,
  title,
  description,
  icon: Icon,
  accent = 'brand',
  defaultOpen = false,
  badge,
  status = 'idle',
  error,
  children,
}: {
  id: string;
  title: string;
  description?: string;
  icon: React.ElementType;
  accent?: 'brand' | 'emerald' | 'amber' | 'rose' | 'indigo' | 'sky' | 'purple';
  defaultOpen?: boolean;
  /** Small right-aligned marker, e.g. "3 of 5 filled" or "Read only". */
  badge?: React.ReactNode;
  status?: SaveStatus;
  error?: string | null;
  children: React.ReactNode;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  const accents: Record<string, string> = {
    brand: 'bg-brand-500/10 text-brand-600',
    emerald: 'bg-emerald-500/10 text-emerald-600',
    amber: 'bg-amber-500/10 text-amber-600',
    rose: 'bg-rose-500/10 text-rose-600',
    indigo: 'bg-indigo-500/10 text-indigo-600',
    sky: 'bg-sky-500/10 text-sky-600',
    purple: 'bg-purple-500/10 text-purple-600',
  };

  return (
    <section className="overflow-hidden rounded-3xl border border-border/80 bg-card shadow-sm">
      <h3>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={`${id}-panel`}
          className="flex w-full items-center gap-3 p-4 text-left transition-colors hover:bg-muted/40 sm:p-5"
        >
          <span className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl', accents[accent])}>
            <Icon className="h-5 w-5" />
          </span>

          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-black text-foreground">{title}</span>
            {description && (
              <span className="block truncate text-[11px] font-medium text-muted-foreground">{description}</span>
            )}
          </span>

          <span className="flex shrink-0 items-center gap-2">
            <SaveIndicator status={status} error={error} />
            {badge}
            <ChevronDown
              className={cn('h-4 w-4 text-muted-foreground transition-transform', open && 'rotate-180')}
            />
          </span>
        </button>
      </h3>

      {open && (
        <div id={`${id}-panel`} className="border-t border-border/60 p-4 sm:p-5">
          {status === 'error' && error && (
            <div className="mb-4 flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs font-medium text-rose-600 dark:text-rose-400">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {children}
        </div>
      )}
    </section>
  );
}

/** Count of filled fields, shown on a collapsed card so a student can see
 *  what still needs attention without opening every section. */
export function FilledBadge({ filled, total }: { filled: number; total: number }) {
  const done = filled >= total;
  return (
    <span
      className={cn(
        'hidden rounded-full px-2 py-0.5 text-[10px] font-extrabold sm:inline-flex',
        done ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'
      )}
    >
      {done ? 'Complete' : `${filled}/${total}`}
    </span>
  );
}

export function ReadOnlyBadge() {
  return (
    <span className="hidden items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-extrabold text-muted-foreground sm:inline-flex">
      <Lock className="h-2.5 w-2.5" /> Read only
    </span>
  );
}

// ---------------------------------------------------------------------------
// Autosave
// ---------------------------------------------------------------------------

export type Validator = (value: unknown) => string | null;

interface AutosaveOptions<T> {
  /** Server state for this section. */
  initial: T;
  /** Sends only the fields that changed. */
  onSave: (patch: Partial<T>) => Promise<unknown>;
  /** Per-field validation. A field that fails is never sent. */
  validators?: Partial<Record<keyof T, Validator>>;
  delayMs?: number;
}

/**
 * Debounced autosave for one section.
 *
 * Two rules matter here:
 *   • Only changed fields are sent, so a section PATCH can never blank out a
 *     field the student didn't touch.
 *   • Server state is re-seeded into the draft only while nothing is pending —
 *     otherwise a background refetch would overwrite what is being typed.
 */
export function useSectionAutosave<T extends Record<string, any>>({
  initial,
  onSave,
  validators,
  delayMs = 1000,
}: AutosaveOptions<T>) {
  const [draft, setDraft] = React.useState<T>(initial);
  const [status, setStatus] = React.useState<SaveStatus>('idle');
  const [error, setError] = React.useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = React.useState<Partial<Record<keyof T, string>>>({});

  const pending = React.useRef<Partial<T>>({});
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlight = React.useRef(false);
  const savedTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Re-seed from the server only when the student has nothing in flight and
  // nothing queued — never clobber in-progress typing.
  React.useEffect(() => {
    if (inFlight.current || Object.keys(pending.current).length > 0) return;
    setDraft(initial);
    // `initial` is rebuilt on every render of the parent, so compare content.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(initial)]);

  const flush = React.useCallback(async () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    const patch = pending.current;
    if (!Object.keys(patch).length) return;

    pending.current = {};
    inFlight.current = true;
    setStatus('saving');
    setError(null);
    try {
      await onSave(patch);
      setStatus('saved');
      if (savedTimer.current) clearTimeout(savedTimer.current);
      savedTimer.current = setTimeout(() => setStatus('idle'), 2500);
    } catch (err) {
      // Put the change back so a retry (or the next edit) resends it rather
      // than silently dropping what the student typed.
      pending.current = { ...patch, ...pending.current };
      setStatus('error');
      setError(extractApiError(err, 'Could not save your changes.'));
    } finally {
      inFlight.current = false;
    }
  }, [onSave]);

  const setField = React.useCallback(
    (field: keyof T, value: T[keyof T]) => {
      setDraft((d) => ({ ...d, [field]: value }));

      const message = validators?.[field]?.(value) ?? null;
      setFieldErrors((e) => {
        const next = { ...e };
        if (message) next[field] = message;
        else delete next[field];
        return next;
      });
      if (message) {
        // Invalid input is held locally: nothing is sent until it is fixed.
        setStatus('idle');
        return;
      }

      pending.current = { ...pending.current, [field]: value } as Partial<T>;
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), delayMs);
    },
    [delayMs, flush, validators]
  );

  // A pending edit must survive unmount — collapsing a card or switching tabs
  // sends it immediately instead of dropping it.
  React.useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
      if (savedTimer.current) clearTimeout(savedTimer.current);
      if (Object.keys(pending.current).length) void flush();
    };
  }, [flush]);

  return { draft, setField, status, error, fieldErrors, flush };
}

// ---------------------------------------------------------------------------
// Validators
// ---------------------------------------------------------------------------

const blank = (v: unknown) => v === null || v === undefined || String(v).trim() === '';

export const validators = {
  phone: (v: unknown) => {
    if (blank(v)) return null;
    const digits = String(v).replace(/[\s-]/g, '').replace(/^\+/, '');
    return /^\d{7,15}$/.test(digits) ? null : 'Enter a valid phone number (7–15 digits).';
  },
  email: (v: unknown) =>
    blank(v) || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(String(v)) ? null : 'Enter a valid email address.',
  aadhaar: (v: unknown) =>
    blank(v) || /^\d{12}$/.test(String(v).replace(/\s/g, '')) ? null : 'Aadhaar must be exactly 12 digits.',
  pin: (v: unknown) => (blank(v) || /^\d{6}$/.test(String(v)) ? null : 'PIN code must be exactly 6 digits.'),
  url: (v: unknown) =>
    blank(v) || /^https?:\/\/\S+\.\S+/.test(String(v)) ? null : 'Links must start with http:// or https://',
  pastDate: (v: unknown) => {
    if (blank(v)) return null;
    const d = new Date(String(v));
    if (Number.isNaN(d.getTime())) return 'Enter a valid date.';
    return d < new Date() ? null : 'Date of birth must be in the past.';
  },
} satisfies Record<string, Validator>;

// ---------------------------------------------------------------------------
// Field wrappers
// ---------------------------------------------------------------------------

export function FieldShell({
  label,
  required,
  hint,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string | null;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-muted-foreground">
        {label}
        {required ? (
          <span className="text-rose-500" aria-hidden>
            *
          </span>
        ) : (
          <span className="font-bold normal-case tracking-normal text-muted-foreground/50">(optional)</span>
        )}
      </label>
      {children}
      {error ? (
        <p className="text-[11px] font-semibold text-rose-600">{error}</p>
      ) : (
        hint && <p className="text-[11px] text-muted-foreground/80">{hint}</p>
      )}
    </div>
  );
}

/** A read-only value pinned inside an editable card, with the reason it is
 *  locked. Used for college email, roll number and the like. */
export function LockedValue({ label, value, reason }: { label: string; value?: string | null; reason?: string }) {
  return (
    <div className="space-y-1 rounded-xl border border-border/60 bg-muted/30 p-3">
      <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest text-muted-foreground">
        <Lock className="h-2.5 w-2.5" /> {label}
      </div>
      <div className={cn('text-xs font-bold', value ? 'text-foreground' : 'italic text-muted-foreground/50')}>
        {value || '—'}
      </div>
      {reason && <p className="text-[10px] text-muted-foreground/70">{reason}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Multi-select chips (closed vocabulary)
// ---------------------------------------------------------------------------

export function MultiSelectChips({
  options,
  value,
  onChange,
  disabled,
}: {
  options: readonly { value: string; label: string }[];
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
}) {
  const selected = new Set(value);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const on = selected.has(option.value);
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            aria-pressed={on}
            onClick={() =>
              onChange(on ? value.filter((v) => v !== option.value) : [...value, option.value])
            }
            className={cn(
              'rounded-full border px-3 py-1.5 text-[11px] font-bold transition-colors disabled:opacity-50',
              on
                ? 'border-brand-500/40 bg-brand-500/15 text-brand-600'
                : 'border-border bg-background text-muted-foreground hover:border-brand-500/30 hover:text-foreground'
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

/** Read-only rendering of a chip list, mapping stored codes to labels. */
export function ChipList({
  value,
  options,
  empty = 'Not provided',
}: {
  value?: string[] | null;
  options?: readonly { value: string; label: string }[];
  empty?: string;
}) {
  if (!value?.length) return <span className="text-xs italic text-muted-foreground/50">{empty}</span>;
  const labelFor = (v: string) => options?.find((o) => o.value === v)?.label ?? v;
  return (
    <div className="flex flex-wrap gap-1.5">
      {value.map((v) => (
        <span
          key={v}
          className="rounded-full border border-border/60 bg-muted/50 px-2.5 py-0.5 text-[11px] font-bold text-foreground"
        >
          {labelFor(v)}
        </span>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Authenticated image
// ---------------------------------------------------------------------------

/**
 * Renders an image served from an authenticated API route.
 *
 * Student photos live behind the same authorisation as their documents, so
 * the browser cannot fetch them with a plain <img src> — no Authorization
 * header is attached to image requests. The bytes are fetched with the API
 * client and shown as a blob URL, which is revoked on unmount.
 */
export function AuthedImage({
  src,
  alt,
  className,
  fallback,
}: {
  src?: string | null;
  alt: string;
  className?: string;
  fallback: React.ReactNode;
}) {
  // The BLOB is what gets cached, never the object URL. An object URL is
  // owned by the component that created it and is revoked on unmount — caching
  // one would hand the next mount a URL that has already been revoked.
  const { data: blob, isError } = useQuery({
    queryKey: ['authed-image', src],
    enabled: !!src,
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      const res = await api.get(src as string, { responseType: 'blob' });
      return res.data as Blob;
    },
  });

  const [objectUrl, setObjectUrl] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!blob) {
      setObjectUrl(null);
      return;
    }
    const url = URL.createObjectURL(blob);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [blob]);

  if (!src || isError || !objectUrl) return <>{fallback}</>;
  return <img src={objectUrl} alt={alt} className={className} />;
}

// ---------------------------------------------------------------------------
// Photo upload with crop
// ---------------------------------------------------------------------------

const CROP_OUTPUT = 512;
const CROP_VIEW = 260;

/**
 * Square-crop dialog for the passport photo.
 *
 * The crop happens in the browser and only the cropped square is uploaded —
 * so the server stores what the student actually chose, and a 12MP camera
 * original never travels over a phone connection.
 */
export function PhotoUploadDialog({
  open,
  onClose,
  onUpload,
}: {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<unknown>;
}) {
  const [image, setImage] = React.useState<HTMLImageElement | null>(null);
  const [fileName, setFileName] = React.useState('photo.jpg');
  const [zoom, setZoom] = React.useState(1);
  const [offset, setOffset] = React.useState({ x: 0, y: 0 });
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const drag = React.useRef<{ x: number; y: number } | null>(null);

  const reset = () => {
    setImage(null);
    setZoom(1);
    setOffset({ x: 0, y: 0 });
    setError(null);
  };

  /** Panning is clamped so the image always covers the crop square — the
   *  student cannot produce a photo with a blank band down one side. */
  const clamp = React.useCallback(
    (next: { x: number; y: number }) => {
      if (!image) return { x: 0, y: 0 };
      const scaleToFill = Math.max(CROP_VIEW / image.width, CROP_VIEW / image.height) * zoom;
      const maxX = Math.max(0, (image.width * scaleToFill - CROP_VIEW) / 2);
      const maxY = Math.max(0, (image.height * scaleToFill - CROP_VIEW) / 2);
      return {
        x: Math.min(maxX, Math.max(-maxX, next.x)),
        y: Math.min(maxY, Math.max(-maxY, next.y)),
      };
    },
    [image, zoom]
  );

  // Draw at the display size; the same maths is replayed at output size on
  // save, so what the student sees in the frame is what gets uploaded.
  const paint = React.useCallback(
    (canvas: HTMLCanvasElement | null, size: number) => {
      if (!canvas || !image) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const scaleToFill = Math.max(size / image.width, size / image.height) * zoom;
      const w = image.width * scaleToFill;
      const h = image.height * scaleToFill;
      const ratio = size / CROP_VIEW;
      ctx.clearRect(0, 0, size, size);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, size, size);
      ctx.drawImage(image, (size - w) / 2 + offset.x * ratio, (size - h) / 2 + offset.y * ratio, w, h);
    },
    [image, zoom, offset]
  );

  // Zooming back out can leave a previously valid pan out of bounds.
  React.useEffect(() => {
    setOffset((current) => {
      const next = clamp(current);
      return next.x === current.x && next.y === current.y ? current : next;
    });
  }, [clamp]);

  React.useEffect(() => {
    paint(canvasRef.current, CROP_VIEW);
  }, [paint]);

  const handleFile = (file?: File) => {
    if (!file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) {
      setError('Choose a JPG, PNG or WEBP image.');
      return;
    }
    setError(null);
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        setImage(img);
        setZoom(1);
        setOffset({ x: 0, y: 0 });
      };
      img.src = String(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    if (!image) return;
    const out = document.createElement('canvas');
    out.width = CROP_OUTPUT;
    out.height = CROP_OUTPUT;
    paint(out, CROP_OUTPUT);

    const blob = await new Promise<Blob | null>((resolve) => out.toBlob(resolve, 'image/jpeg', 0.9));
    if (!blob) {
      setError('Could not process that image. Try another one.');
      return;
    }
    const base = fileName.replace(/\.[^.]+$/, '') || 'photo';
    setBusy(true);
    setError(null);
    try {
      await onUpload(new File([blob], `${base}.jpg`, { type: 'image/jpeg' }));
      reset();
      onClose();
    } catch (err) {
      setError(extractApiError(err, 'Upload failed. Please try again.'));
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md space-y-4 rounded-3xl border border-border bg-card p-5 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-black text-foreground">Profile photograph</h4>
            <p className="text-[11px] text-muted-foreground">Passport style — drag to position, slide to zoom.</p>
          </div>
          <button
            type="button"
            onClick={() => {
              reset();
              onClose();
            }}
            className="rounded-full p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs font-medium text-rose-600">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> <span>{error}</span>
          </div>
        )}

        {image ? (
          <div className="space-y-3">
            <div className="flex justify-center">
              <canvas
                ref={canvasRef}
                width={CROP_VIEW}
                height={CROP_VIEW}
                className="cursor-move touch-none rounded-2xl border border-border"
                onPointerDown={(e) => {
                  drag.current = { x: e.clientX - offset.x, y: e.clientY - offset.y };
                  e.currentTarget.setPointerCapture(e.pointerId);
                }}
                onPointerMove={(e) => {
                  if (!drag.current) return;
                  setOffset(clamp({ x: e.clientX - drag.current.x, y: e.clientY - drag.current.y }));
                }}
                onPointerUp={() => {
                  drag.current = null;
                }}
              />
            </div>

            <div className="flex items-center gap-3">
              <ZoomIn className="h-4 w-4 shrink-0 text-muted-foreground" />
              <input
                type="range"
                min={1}
                max={3}
                step={0.01}
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
                className="w-full accent-brand-600"
                aria-label="Zoom"
              />
              <button
                type="button"
                onClick={() => {
                  setZoom(1);
                  setOffset({ x: 0, y: 0 });
                }}
                className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Reset crop"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={reset} disabled={busy}>
                Choose another
              </Button>
              <Button size="sm" onClick={handleSave} isLoading={busy}>
                <Check className="mr-1 h-3.5 w-3.5" /> Save photo
              </Button>
            </div>
          </div>
        ) : (
          <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-border p-8 text-center hover:border-brand-500/50 hover:bg-muted/30">
            <Upload className="h-6 w-6 text-muted-foreground" />
            <span className="text-xs font-bold text-foreground">Choose a photo</span>
            <span className="text-[11px] text-muted-foreground">JPG, PNG or WEBP</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </label>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small shared bits
// ---------------------------------------------------------------------------

export function AutoInput({
  value,
  onCommit,
  error,
  ...props
}: Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> & {
  value?: string | number | null;
  onCommit: (value: string) => void;
  error?: string | null;
}) {
  return <Input {...props} value={value ?? ''} error={!!error} onChange={(e) => onCommit(e.target.value)} />;
}

export function AutoTextArea({
  value,
  onCommit,
  rows = 3,
  error,
  ...props
}: Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'value' | 'onChange'> & {
  value?: string | null;
  onCommit: (value: string) => void;
  error?: string | null;
}) {
  return (
    <textarea
      {...props}
      rows={rows}
      value={value ?? ''}
      onChange={(e) => onCommit(e.target.value)}
      className={cn(
        'w-full rounded-xl border bg-background p-3 text-xs placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring',
        error ? 'border-rose-500' : 'border-input'
      )}
    />
  );
}

export function AutoSelect({
  value,
  onCommit,
  options,
  placeholder = 'Select…',
  ...props
}: Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'value' | 'onChange'> & {
  value?: string | null;
  onCommit: (value: string) => void;
  options: readonly string[] | readonly { value: string; label: string }[];
  placeholder?: string;
}) {
  const normalised = options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o));
  return (
    <select
      {...props}
      value={value ?? ''}
      onChange={(e) => onCommit(e.target.value)}
      className="h-10 w-full rounded-xl border border-input bg-background px-3 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-ring"
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
