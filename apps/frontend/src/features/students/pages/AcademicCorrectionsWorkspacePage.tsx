import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentService, AcademicCorrection, AcademicCorrectionReview } from '../services/student.service';
import { profileService } from '../services/profile.service';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Button } from '@/shared/components/ui/Button';
import { RequestCorrectionModal } from '../components/RequestCorrectionModal';
import {
  FileCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  FileText,
  Plus,
  Send,
  Download,
  History,
} from 'lucide-react';
import { cn } from '@/shared/utils/cn';


export function AcademicCorrectionsWorkspacePage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isStudent = user?.roles.includes('STUDENT') ?? false;

  const [newModalOpen, setNewModalOpen] = React.useState(false);
  const [selectedReqId, setSelectedReqId] = React.useState<string | null>(null);

  // Review form state for Counsellors
  const [reviewRemarks, setReviewRemarks] = React.useState('');
  const [reviewStatus, setReviewStatus] = React.useState<'APPROVED' | 'REJECTED' | 'NEED_MORE_INFO'>('APPROVED');

  // Clarification form state for Students
  const [clarificationRemarks, setClarificationRemarks] = React.useState('');
  const [clarificationFile, setClarificationFile] = React.useState<File | null>(null);
  const [uploadingFile, setUploadingFile] = React.useState(false);

  // Fetch correction requests
  const {
    data: requests = [],
    isLoading,
    error,
  } = useQuery<AcademicCorrection[]>({
    queryKey: isStudent ? ['students', 'me', 'academic-corrections'] : ['students', 'academic-corrections', 'caseload'],
    queryFn: () => (isStudent ? studentService.getMyCorrectionRequests() : studentService.getCaseloadCorrectionRequests()),
  });

  const selectedRequest = requests.find((r) => r.id === selectedReqId) || requests[0] || null;

  React.useEffect(() => {
    if (!selectedReqId && requests.length > 0) {
      setSelectedReqId(requests[0].id);
    }
  }, [requests, selectedReqId]);

  // Review mutation for Counsellors
  const reviewMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: AcademicCorrectionReview }) =>
      studentService.reviewCorrectionRequest(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', 'academic-corrections'] });
      queryClient.invalidateQueries({ queryKey: ['students', 'me', 'academic-corrections'] });
      setReviewRemarks('');
    },
  });

  // Clarification mutation for Students
  const clarificationMutation = useMutation({
    mutationFn: async ({ id, remarks, file }: { id: string; remarks: string; file: File | null }) => {
      let docId: string | undefined = undefined;
      if (file) {
        setUploadingFile(true);
        const doc = await profileService.uploadDocument(file, 'OTHER', 'Correction Clarification Document');
        docId = doc.id;
      }
      return studentService.submitCorrectionClarification(id, { remarks, document_id: docId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', 'academic-corrections'] });
      queryClient.invalidateQueries({ queryKey: ['students', 'me', 'academic-corrections'] });
      setClarificationRemarks('');
      setClarificationFile(null);
      setUploadingFile(false);
    },
    onError: () => {
      setUploadingFile(false);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 rounded-3xl" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-96 rounded-3xl lg:col-span-1" />
          <Skeleton className="h-96 rounded-3xl lg:col-span-2" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Unable to load Correction Requests"
        description="Failed to connect to backend service."
      />
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Student 360 Portal', to: '/student-360/personal' }, { label: 'Correction Requests' }]} />

      {/* WORKSPACE HEADER */}
      <div className="rounded-3xl border border-border/80 bg-gradient-to-r from-card via-muted/30 to-card p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-brand-500/30 bg-brand-500/10 text-brand-600 font-bold">
                {isStudent ? 'Student Request Portal' : 'Counsellor Review Desk'}
              </Badge>
              <span className="text-xs font-mono text-muted-foreground">{requests.length} Requests Total</span>
            </div>
            <h1 className="text-2xl font-black text-foreground">Academic Correction Requests Workspace</h1>
            <p className="text-xs text-muted-foreground">
              {isStudent
                ? 'Track formal correction requests, upload clarification evidence, and view status timeline.'
                : 'Review assigned student academic correction requests, compare evidence, and approve or reject.'}
            </p>
          </div>

          {isStudent && (
            <Button size="sm" className="font-bold shrink-0" onClick={() => setNewModalOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" /> New Correction Request
            </Button>
          )}
        </div>
      </div>

      {/* WORKSPACE BODY */}
      {requests.length === 0 ? (
        <EmptyState
          icon={FileCheck}
          title="No Correction Requests Found"
          description={
            isStudent
              ? "You haven't submitted any academic record correction requests yet."
              : 'There are no pending or reviewed academic correction requests on your caseload.'
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* REQUESTS LIST SIDEBAR */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-xs font-black uppercase text-muted-foreground tracking-wider px-1">
              Requests ({requests.length})
            </h2>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {requests.map((req) => {
                const isSelected = selectedRequest?.id === req.id;
                return (
                  <div
                    key={req.id}
                    onClick={() => setSelectedReqId(req.id)}
                    className={cn(
                      'p-4 rounded-2xl border transition-all cursor-pointer space-y-2',
                      isSelected
                        ? 'border-brand-600 bg-brand-500/5 shadow-md ring-1 ring-brand-500/30'
                        : 'border-border/70 bg-card hover:bg-accent/40'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="font-bold text-[10px]">
                        {req.section_name}
                      </Badge>
                      <StatusBadge status={req.status} />
                    </div>

                    {!isStudent && (
                      <p className="text-xs font-bold text-foreground">
                        {req.student_name} <span className="text-[10px] font-mono text-muted-foreground">({req.student_roll})</span>
                      </p>
                    )}

                    <p className="text-xs font-medium text-foreground line-clamp-2 leading-relaxed">
                      {req.description}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono pt-1 border-t border-border/40">
                      <span>{new Date(req.created_at).toLocaleDateString()}</span>
                      <span>{req.logs?.length || 1} Timeline events</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* REQUEST DETAIL & TIMELINE PANEL */}
          {selectedRequest && (
            <div className="lg:col-span-2 space-y-6">
              <Card className="rounded-3xl border-border/80 shadow-xl overflow-hidden">
                <CardHeader className="border-b border-border/60 pb-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="font-bold border-brand-500/30 bg-brand-500/10 text-brand-600">
                          {selectedRequest.section_name}
                        </Badge>
                        <StatusBadge status={selectedRequest.status} size="lg" />
                      </div>
                      <CardTitle className="text-lg font-black">
                        Request ID: <span className="font-mono text-sm">{selectedRequest.id.slice(0, 8)}...</span>
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Submitted on {new Date(selectedRequest.created_at).toLocaleString()}
                        {selectedRequest.counsellor_name && ` • Assigned to ${selectedRequest.counsellor_name}`}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-6 pt-5">
                  {/* VALUES & DESCRIPTION */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3.5 rounded-2xl bg-muted/20 border border-border/60">
                      <span className="text-[10px] font-black uppercase text-muted-foreground block">
                        Current Value on Record
                      </span>
                      <span className="text-sm font-bold text-foreground mt-0.5 block">
                        {selectedRequest.current_value || 'Not specified'}
                      </span>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-brand-500/5 border border-brand-500/20">
                      <span className="text-[10px] font-black uppercase text-brand-600 block">
                        Requested / Correct Value
                      </span>
                      <span className="text-sm font-bold text-brand-600 mt-0.5 block">
                        {selectedRequest.proposed_value || 'Not specified'}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-black uppercase text-muted-foreground block">
                      Description &amp; Reason
                    </span>
                    <p className="text-xs leading-relaxed text-foreground bg-muted/20 p-3.5 rounded-2xl border border-border/60">
                      {selectedRequest.description}
                    </p>
                  </div>

                  {/* ATTACHED DOCUMENT DOWNLOAD */}
                  {selectedRequest.document_id && (
                    <div className="flex items-center justify-between p-3.5 rounded-2xl border border-border/70 bg-card">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className="h-5 w-5 text-brand-500 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-foreground truncate">
                            {selectedRequest.document_name || 'Supporting Document'}
                          </p>
                          <p className="text-[10px] text-muted-foreground">Uploaded with request</p>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="font-bold text-xs"
                        onClick={() =>
                          profileService.downloadDocument(
                            selectedRequest.student_id,
                            selectedRequest.document_id!,
                            selectedRequest.document_name || 'document.pdf'
                          )
                        }
                      >
                        <Download className="mr-1 h-3.5 w-3.5" /> Download Evidence
                      </Button>
                    </div>
                  )}

                  {/* STUDENT CLARIFICATION RESPONSE BOX (WHEN NEED_MORE_INFO) */}
                  {isStudent && selectedRequest.status === 'NEED_MORE_INFO' && (
                    <div className="rounded-2xl border border-amber-500/40 bg-amber-500/5 p-4 space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-700">
                        <HelpCircle className="h-4 w-4 text-amber-600" />
                        <span>Action Required: Provide Requested Clarification</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Your counsellor requested additional details: <strong>"{selectedRequest.counsellor_remarks}"</strong>
                      </p>

                      <textarea
                        rows={3}
                        value={clarificationRemarks}
                        onChange={(e) => setClarificationRemarks(e.target.value)}
                        placeholder="Provide details or comments requested by your counsellor..."
                        className="w-full rounded-xl border border-input bg-background p-3 text-xs focus:ring-2 focus:ring-amber-500"
                      />

                      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                        <input
                          type="file"
                          id="clarification-file"
                          onChange={(e) => setClarificationFile(e.target.files?.[0] || null)}
                          className="text-xs text-muted-foreground file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-brand-500/10 file:text-brand-600 hover:file:bg-brand-500/20"
                        />
                        <Button
                          size="sm"
                          isLoading={clarificationMutation.isPending || uploadingFile}
                          disabled={!clarificationRemarks.trim() && !clarificationFile}
                          onClick={() =>
                            clarificationMutation.mutate({
                              id: selectedRequest.id,
                              remarks: clarificationRemarks,
                              file: clarificationFile,
                            })
                          }
                        >
                          <Send className="mr-1.5 h-3.5 w-3.5" /> Resubmit Clarification
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* COUNSELLOR REVIEW PANEL (FOR STAFF/COUNSELLORS) */}
                  {!isStudent && ['SUBMITTED', 'ASSIGNED', 'UNDER_REVIEW', 'NEED_MORE_INFO'].includes(selectedRequest.status) && (
                    <div className="rounded-2xl border border-brand-500/30 bg-brand-500/5 p-4 space-y-3">
                      <span className="text-xs font-black uppercase text-brand-600 block">
                        Counsellor Review Action
                      </span>

                      <div className="space-y-1">
                        <label className="text-xs font-bold text-foreground">Review Remarks / Instructions</label>
                        <textarea
                          rows={3}
                          value={reviewRemarks}
                          onChange={(e) => setReviewRemarks(e.target.value)}
                          placeholder="Provide approval remarks or specify required clarification documents..."
                          className="w-full rounded-xl border border-input bg-background p-3 text-xs focus:ring-2 focus:ring-brand-500"
                        />
                      </div>

                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <Button
                          size="sm"
                          className="bg-emerald-600 hover:bg-emerald-700 font-bold"
                          isLoading={reviewMutation.isPending && reviewStatus === 'APPROVED'}
                          onClick={() => {
                            setReviewStatus('APPROVED');
                            reviewMutation.mutate({
                              id: selectedRequest.id,
                              data: { status: 'APPROVED', remarks: reviewRemarks },
                            });
                          }}
                        >
                          <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Approve Correction
                        </Button>

                        <Button
                          size="sm"
                          variant="outline"
                          className="border-amber-500 text-amber-700 hover:bg-amber-500/10 font-bold"
                          isLoading={reviewMutation.isPending && reviewStatus === 'NEED_MORE_INFO'}
                          onClick={() => {
                            setReviewStatus('NEED_MORE_INFO');
                            reviewMutation.mutate({
                              id: selectedRequest.id,
                              data: { status: 'NEED_MORE_INFO', remarks: reviewRemarks },
                            });
                          }}
                        >
                          <HelpCircle className="mr-1.5 h-3.5 w-3.5 text-amber-600" /> Request Clarification
                        </Button>

                        <Button
                          size="sm"
                          variant="destructive"
                          isLoading={reviewMutation.isPending && reviewStatus === 'REJECTED'}
                          onClick={() => {
                            setReviewStatus('REJECTED');
                            reviewMutation.mutate({
                              id: selectedRequest.id,
                              data: { status: 'REJECTED', remarks: reviewRemarks },
                            });
                          }}
                        >
                          <XCircle className="mr-1.5 h-3.5 w-3.5" /> Reject Request
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* CRM TIMELINE AUDIT LOG HISTORY */}
                  <div className="space-y-3 border-t border-border/60 pt-4">
                    <span className="text-xs font-black uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                      <History className="h-4 w-4 text-brand-500" /> CRM Audit Timeline &amp; History
                    </span>

                    <div className="space-y-3 relative pl-4 border-l-2 border-border/60">
                      {selectedRequest.logs?.map((log) => (
                        <div key={log.id} className="relative space-y-1">
                          <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-brand-500 ring-4 ring-background" />

                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-foreground">
                              {log.actor_name || 'System User'}{' '}
                              <span className="font-normal text-muted-foreground">({log.action})</span>
                            </span>
                            <span className="font-mono text-[10px] text-muted-foreground">
                              {new Date(log.created_at).toLocaleString()}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            {log.from_status && (
                              <Badge variant="outline" className="text-[10px]">
                                {log.from_status}
                              </Badge>
                            )}
                            <span className="text-xs text-muted-foreground">➔</span>
                            <Badge variant="secondary" className="text-[10px] font-bold">
                              {log.to_status}
                            </Badge>
                          </div>

                          {log.remarks && (
                            <p className="text-xs text-muted-foreground italic bg-muted/10 p-2 rounded-xl border border-border/40 mt-1">
                              "{log.remarks}"
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* NEW REQUEST MODAL */}
      <RequestCorrectionModal
        open={newModalOpen}
        onClose={() => setNewModalOpen(false)}
      />
    </div>
  );
}

function StatusBadge({ status, size = 'sm' }: { status: string; size?: 'sm' | 'lg' }) {
  let variant: 'secondary' | 'outline' | 'warning' | 'success' | 'destructive' = 'secondary';
  let label = status;

  switch (status) {
    case 'SUBMITTED':
      variant = 'outline';
      break;
    case 'UNDER_REVIEW':
    case 'ASSIGNED':
      variant = 'warning';
      break;
    case 'NEED_MORE_INFO':
      variant = 'warning';
      label = 'Need Clarification';
      break;
    case 'APPROVED':
      variant = 'success';
      break;
    case 'REJECTED':
      variant = 'destructive';
      break;
  }

  return (
    <Badge variant={variant} className={cn('font-bold uppercase tracking-wider', size === 'lg' ? 'text-xs px-2.5 py-0.5' : 'text-[10px]')}>
      {label}
    </Badge>
  );
}
