import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { counsellingService, SessionCreateData } from '../services/counselling.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/shared/components/ui/Card';
import { AlertCircle, Plus, Trash2, ArrowLeft } from 'lucide-react';
import { useState } from 'react';

export function NewSessionPage() {
  const [searchParams] = useSearchParams();
  const studentIdParam = searchParams.get('student_id') || '';
  const navigate = useNavigate();

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SessionCreateData>({
    defaultValues: {
      student_id: studentIdParam,
      session_date: new Date().toISOString().split('T')[0],
      session_type: 'ACADEMIC',
      mode: 'IN_PERSON',
      observations: '',
      follow_up_required: false,
      risk_assessment: 'NONE',
      confidential: false,
      action_items: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'action_items',
  });

  const followUpRequired = watch('follow_up_required');
  const observationsValue = watch('observations') || '';

  const onSubmit = async (data: SessionCreateData) => {
    try {
      setErrorMsg(null);
      setIsSubmitting(true);
      await counsellingService.createSession(data);
      navigate(`/students/${data.student_id}`);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.error?.message || 'Failed to record session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
      <Breadcrumbs
        items={[
          { label: 'Counselling Sessions', href: '/counselling/sessions' },
          { label: 'New Session Record' },
        ]}
      />

      <PageHeader
        title="Record Counselling Session"
        subtitle="Create an immutable, structured record of a counselling interaction (§23)"
        actions={
          <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-6 max-w-4xl">
        {errorMsg && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-4 text-xs font-medium text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Session Details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Student ID / Roll</label>
              <Input {...register('student_id', { required: 'Student is required' })} placeholder="Enter Student ID" />
              {errors.student_id && <p className="text-xs text-destructive">{errors.student_id.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Session Date</label>
              <Input type="date" {...register('session_date', { required: true })} />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Session Type</label>
              <select {...register('session_type')} className="w-full h-9 rounded-md border bg-transparent px-3 text-xs">
                <option value="ACADEMIC">ACADEMIC</option>
                <option value="PERSONAL">PERSONAL</option>
                <option value="BEHAVIOURAL">BEHAVIOURAL</option>
                <option value="CAREER">CAREER</option>
                <option value="HEALTH">HEALTH</option>
                <option value="FINANCIAL">FINANCIAL</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Interaction Mode</label>
              <select {...register('mode')} className="w-full h-9 rounded-md border bg-transparent px-3 text-xs">
                <option value="IN_PERSON">IN_PERSON</option>
                <option value="PHONE">PHONE</option>
                <option value="VIDEO_CALL">VIDEO_CALL</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Observations Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Observations & Discussion Notes</CardTitle>
            <span className={`text-xs font-medium ${observationsValue.length < 50 ? 'text-amber-600' : 'text-emerald-600'}`}>
              {observationsValue.length} / 50 min characters
            </span>
          </CardHeader>
          <CardContent className="space-y-2">
            <textarea
              {...register('observations', {
                required: 'Observations are required',
                minLength: { value: 50, message: 'Minimum 50 characters required' },
              })}
              rows={6}
              placeholder="Record detailed notes of the counselling interaction, discussions, student response, and specific recommendations..."
              className="w-full rounded-md border bg-transparent p-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            />
            {errors.observations && (
              <p className="text-xs text-destructive font-medium">{errors.observations.message}</p>
            )}
          </CardContent>
        </Card>

        {/* Action Items & Follow-up */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Action Items & Follow-up</CardTitle>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ description: '', due_date: new Date().toISOString().split('T')[0] })}
            >
              <Plus className="mr-1 h-3.5 w-3.5" /> Add Action Item
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {fields.map((field, index) => (
              <div key={field.id} className="flex items-center gap-2">
                <Input
                  {...register(`action_items.${index}.description` as const, { required: true })}
                  placeholder="Action item description..."
                  className="flex-1"
                />
                <Input
                  type="date"
                  {...register(`action_items.${index}.due_date` as const, { required: true })}
                  className="w-40"
                />
                <Button type="button" variant="ghost" size="icon" onClick={() => remove(index)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}

            <div className="flex items-center gap-4 pt-4 border-t">
              <label className="flex items-center gap-2 text-xs font-medium cursor-pointer">
                <input type="checkbox" {...register('follow_up_required')} className="rounded" />
                Follow-up required
              </label>

              {followUpRequired && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Follow-up Date:</span>
                  <Input type="date" {...register('follow_up_date')} className="w-40" />
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting Record...' : 'Submit Session Record'}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </AppShell>
  );
}
