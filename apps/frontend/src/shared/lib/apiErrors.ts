import type { FieldValues, Path, UseFormSetError } from 'react-hook-form';
import type { ApiErrorResponse } from '@scms/types';

/**
 * Maps backend 422 `error.details[].field` entries onto react-hook-form
 * fields (field paths are dot-joined server-side, e.g. "student_details.roll_number",
 * so they line up 1:1 with react-hook-form's dot-path field names).
 *
 * Returns a general banner message to show only when no field-specific
 * errors could be applied (e.g. a 409 conflict or network failure) — when
 * field errors are set, the inline messages are enough on their own.
 */
export function applyServerFieldErrors<T extends FieldValues>(
  err: any,
  setError: UseFormSetError<T>,
  /** Rewrites a backend field path (e.g. "student_details.roll_number") to the
   * form's own field name (e.g. "roll_number") when the form is flatter than
   * the request payload it builds. Defaults to using the path unchanged. */
  mapField: (field: string) => string = (field) => field
): string | null {
  const data: ApiErrorResponse | undefined = err?.response?.data;
  const details = data?.error?.details;

  if (Array.isArray(details) && details.length > 0) {
    let appliedAny = false;
    for (const detail of details) {
      if (detail?.field && detail?.message) {
        setError(mapField(detail.field) as Path<T>, { type: 'server', message: detail.message });
        appliedAny = true;
      }
    }
    if (appliedAny) return null;
  }

  return data?.error?.message || 'Something went wrong. Please check the form and try again.';
}
