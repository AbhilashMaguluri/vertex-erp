import * as React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parentService, ParentCommunicationCreateData, ParentCommunication } from '../services/parent.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { PhoneCall, CheckCircle2 } from 'lucide-react';

export function ParentCommunicationPage() {
  const queryClient = useQueryClient();
  const [selectedStudentId, setSelectedStudentId] = React.useState<string>('');
  const [feedbackMsg, setFeedbackMsg] = React.useState<string | null>(null);

  const { data: communications, isLoading } = useQuery<ParentCommunication[]>({
    queryKey: ['parents', selectedStudentId],
    queryFn: () => parentService.getStudentCommunications(selectedStudentId),
    enabled: !!selectedStudentId,
  });

  const { register, handleSubmit, reset } = useForm<ParentCommunicationCreateData>({
    defaultValues: {
      student_id: selectedStudentId,
      communication_date: new Date().toISOString().split('T')[0],
      mode: 'PHONE_CALL',
      parent_name: '',
      relation: 'Father',
      contact_number: '',
      summary: '',
      outcome: 'POSITIVE',
    },
  });

  const logMutation = useMutation({
    mutationFn: (data: ParentCommunicationCreateData) => parentService.logCommunication(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents', selectedStudentId] });
      setFeedbackMsg('Parent communication logged successfully.');
      reset();
      setTimeout(() => setFeedbackMsg(null), 3000);
    },
    onError: (err: any) => {
      setFeedbackMsg(err?.response?.data?.error?.message || 'Could not log communication — verify Student ID.');
    },
  });

  const onSubmit = (data: ParentCommunicationCreateData) => {
    logMutation.mutate({ ...data, student_id: selectedStudentId });
  };

  return (
    <>
      <Breadcrumbs items={[{ label: 'Parent Communication Log' }]} />

      <PageHeader
        title="Parent Communication Log"
        subtitle="Track phone calls, in-person discussions, and outcome follow-ups with parents or guardians"
      />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Column */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <PhoneCall className="h-4 w-4 text-primary" /> Log Interaction
            </CardTitle>
            <CardDescription>Record call summary and guardian details</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              {feedbackMsg && (
                <div
                  className={`flex items-center gap-2.5 rounded-xl border p-3.5 text-xs font-medium ${
                    logMutation.isError
                      ? 'bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400'
                      : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300'
                  }`}
                >
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{feedbackMsg}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Student ID / Roll No</label>
                <Input
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  placeholder="Enter Student ID to filter history"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Date of Contact</label>
                <Input type="date" {...register('communication_date')} />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Communication Mode</label>
                <select {...register('mode')} className="w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold">
                  <option value="PHONE_CALL">PHONE_CALL — Voice Call</option>
                  <option value="IN_PERSON">IN_PERSON — Office Visit</option>
                  <option value="EMAIL">EMAIL — Formal Email</option>
                  <option value="VIDEO_CALL">VIDEO_CALL — Remote Video</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Parent Name</label>
                  <Input {...register('parent_name', { required: true })} placeholder="Full name" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Relation</label>
                  <select {...register('relation')} className="w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold">
                    <option value="Father">Father</option>
                    <option value="Mother">Mother</option>
                    <option value="Guardian">Guardian</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Contact Number</label>
                <Input {...register('contact_number', { required: true })} placeholder="+1 (555) 000-0000" />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Interaction Summary</label>
                <textarea
                  {...register('summary', { required: true, minLength: 10 })}
                  rows={4}
                  placeholder="Record key topics discussed and commitments made..."
                  className="w-full rounded-xl border border-input bg-background p-3 text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Outcome</label>
                <select {...register('outcome')} className="w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold">
                  <option value="POSITIVE">POSITIVE — Cooperative</option>
                  <option value="NEUTRAL">NEUTRAL — Informed</option>
                  <option value="CONCERNING">CONCERNING — Escalation Required</option>
                  <option value="UNRESPONSIVE">UNRESPONSIVE — Unreachable</option>
                </select>
              </div>

              <Button type="submit" className="w-full" isLoading={logMutation.isPending} disabled={!selectedStudentId.trim()}>
                Save Communication Log
              </Button>
            </CardContent>
          </form>
        </Card>

        {/* History Column */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-bold text-foreground tracking-tight">Interaction History</h3>

          {!selectedStudentId ? (
            <EmptyState
              icon={PhoneCall}
              title="No student selected"
              description="Enter a Student ID in the form to filter and view past communication logs."
            />
          ) : isLoading ? (
            <Skeleton className="h-48 rounded-xl" />
          ) : !communications || communications.length === 0 ? (
            <EmptyState
              icon={PhoneCall}
              title="No Communications Recorded"
              description="No parent interaction logs recorded for this student yet."
            />
          ) : (
            <div className="space-y-3">
              {communications.map((c) => (
                <Card key={c.id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-foreground">{c.parent_name}</span>
                        <span className="text-xs text-muted-foreground">({c.relation})</span>
                        <Badge variant="outline">{c.mode}</Badge>
                      </div>
                      <Badge variant={c.outcome === 'CONCERNING' ? 'destructive' : 'success'}>
                        {c.outcome}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{c.summary}</p>
                    <div className="text-[11px] font-mono text-muted-foreground pt-2 border-t border-border/60 flex justify-between">
                      <span>Phone: {c.contact_number}</span>
                      <span>Date: {c.communication_date}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
