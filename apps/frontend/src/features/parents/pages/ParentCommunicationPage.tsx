import * as React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { parentService, ParentCommunicationCreateData, ParentCommunication } from '../services/parent.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { PhoneCall, CheckCircle2 } from 'lucide-react';

export function ParentCommunicationPage() {
  const queryClient = useQueryClient();
  const [selectedStudentId, setSelectedStudentId] = React.useState<string>('stu-1');
  const [feedbackMsg, setFeedbackMsg] = React.useState<string | null>(null);

  const { data: communications, isLoading } = useQuery<ParentCommunication[]>({
    queryKey: ['parents', selectedStudentId],
    queryFn: () => parentService.getStudentCommunications(selectedStudentId),
  });

  const { register, handleSubmit, reset } = useForm<ParentCommunicationCreateData>({
    defaultValues: {
      student_id: selectedStudentId,
      communication_date: new Date().toISOString().split('T')[0],
      mode: 'PHONE_CALL',
      parent_name: 'Sridhar Kumar',
      relation: 'Father',
      contact_number: '+91 9876543210',
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
  });

  const onSubmit = (data: ParentCommunicationCreateData) => {
    logMutation.mutate({ ...data, student_id: selectedStudentId });
  };

  return (
    <AppShell userRole="COUNSELLOR" userName="Dr. Priya Sharma">
      <Breadcrumbs items={[{ label: 'Parent Communication' }]} />

      <PageHeader
        title="Parent Communication Log"
        subtitle="Record call summaries, in-person meetings, and outcomes with parents/guardians (§24)"
      />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Column */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <PhoneCall className="h-4 w-4 text-primary" /> Log New Interaction
            </CardTitle>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              {feedbackMsg && (
                <div className="flex items-center gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-xs font-medium text-emerald-800">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{feedbackMsg}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Student ID</label>
                <Input
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  placeholder="Student ID"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Date of Contact</label>
                <Input type="date" {...register('communication_date')} />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Communication Mode</label>
                <select {...register('mode')} className="w-full h-9 rounded-md border bg-transparent px-3 text-xs">
                  <option value="PHONE_CALL">PHONE_CALL</option>
                  <option value="IN_PERSON">IN_PERSON</option>
                  <option value="EMAIL">EMAIL</option>
                  <option value="VIDEO_CALL">VIDEO_CALL</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Parent Name</label>
                  <Input {...register('parent_name', { required: true })} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold">Relation</label>
                  <select {...register('relation')} className="w-full h-9 rounded-md border bg-transparent px-3 text-xs">
                    <option value="Father">Father</option>
                    <option value="Mother">Mother</option>
                    <option value="Guardian">Guardian</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Contact Number</label>
                <Input {...register('contact_number', { required: true })} />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Interaction Summary</label>
                <textarea
                  {...register('summary', { required: true, minLength: 10 })}
                  rows={4}
                  placeholder="Record summary of discussion..."
                  className="w-full rounded-md border bg-transparent p-2 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold">Outcome</label>
                <select {...register('outcome')} className="w-full h-9 rounded-md border bg-transparent px-3 text-xs">
                  <option value="POSITIVE">POSITIVE</option>
                  <option value="NEUTRAL">NEUTRAL</option>
                  <option value="CONCERNING">CONCERNING</option>
                  <option value="UNRESPONSIVE">UNRESPONSIVE</option>
                </select>
              </div>

              <Button type="submit" className="w-full" disabled={logMutation.isPending}>
                {logMutation.isPending ? 'Saving Log...' : 'Save Communication Log'}
              </Button>
            </CardContent>
          </form>
        </Card>

        {/* History Column */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-base font-semibold">Interaction History</h3>

          {isLoading ? (
            <Skeleton className="h-48" />
          ) : !communications || communications.length === 0 ? (
            <EmptyState
              icon={PhoneCall}
              title="No Communications Recorded"
              description="No parent interaction logs recorded for this student yet."
            />
          ) : (
            <div className="space-y-4">
              {communications.map((c) => (
                <div key={c.id} className="rounded-lg border bg-card p-4 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{c.parent_name}</span>
                      <span className="text-xs text-muted-foreground">({c.relation})</span>
                      <Badge variant="outline">{c.mode}</Badge>
                    </div>
                    <Badge variant={c.outcome === 'CONCERNING' ? 'danger' : 'success'}>{c.outcome}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{c.summary}</p>
                  <div className="text-[11px] text-muted-foreground pt-1 border-t flex justify-between">
                    <span>Contact: {c.contact_number}</span>
                    <span>Date: {c.communication_date}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
