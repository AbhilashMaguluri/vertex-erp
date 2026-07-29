import * as React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { studentService, AcademicCorrectionCreate } from '../services/student.service';
import { profileService } from '../services/profile.service';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Upload, CheckCircle2, AlertCircle, X, ShieldAlert } from 'lucide-react';

interface RequestCorrectionModalProps {
  open: boolean;
  onClose: () => void;
  /** Section context pre-selected from card (e.g. "Attendance", "SGPA", "Backlogs", "Department") */
  sectionName?: string;
  currentValue?: string;
}

export function RequestCorrectionModal({
  open,
  onClose,
  sectionName = 'Academic Record',
  currentValue = '',
}: RequestCorrectionModalProps) {
  const queryClient = useQueryClient();
  const [proposedValue, setProposedValue] = React.useState('');
  const [currVal, setCurrVal] = React.useState(currentValue);
  const [description, setDescription] = React.useState('');

  const [uploading, setUploading] = React.useState(false);
  const [uploadedDocId, setUploadedDocId] = React.useState<string | null>(null);
  const [uploadedDocName, setUploadedDocName] = React.useState<string | null>(null);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  React.useEffect(() => {
    setCurrVal(currentValue);
  }, [currentValue]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setErrorMsg(null);
    try {
      const doc = await profileService.uploadDocument(
        file,
        'OTHER',
        `Supporting Document - ${sectionName} Correction`
      );
      setUploadedDocId(doc.id);
      setUploadedDocName(doc.original_filename);
    } catch (err: any) {
      setErrorMsg('Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const submitMutation = useMutation({
    mutationFn: (data: AcademicCorrectionCreate) => studentService.createCorrectionRequest(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', 'me', 'academic-corrections'] });
      queryClient.invalidateQueries({ queryKey: ['students', 'academic-corrections'] });
      onClose();
      // Reset form
      setProposedValue('');
      setDescription('');
      setUploadedDocId(null);
      setUploadedDocName(null);
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Failed to submit correction request.');
    },
  });

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || description.length < 10) {
      setErrorMsg('Please provide a detailed description (at least 10 characters).');
      return;
    }
    submitMutation.mutate({
      section_name: sectionName,
      current_value: currVal,
      proposed_value: proposedValue,
      description: description.trim(),
      document_id: uploadedDocId || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
      <Card className="w-full max-w-lg border-border bg-card shadow-2xl overflow-hidden">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3 border-b border-border/60">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-500" />
              <CardTitle className="text-base font-black">Request Academic Record Correction</CardTitle>
            </div>
            <CardDescription className="text-xs mt-1">
              Submit a formal request to your assigned counsellor to review and correct your record.
            </CardDescription>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-accent hover:text-foreground cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-4">
            {errorMsg && (
              <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 p-3 text-xs font-bold text-rose-600 border border-rose-500/20">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Context-locked section badge */}
            <div className="rounded-xl border border-border/80 bg-muted/30 p-3.5 space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-muted-foreground block">
                Target Academic Section
              </span>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-bold text-brand-600 border-brand-500/30 bg-brand-500/10">
                  {sectionName}
                </Badge>
                <span className="text-xs text-muted-foreground italic">(Auto-selected)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-bold text-foreground">Current Value on Record</label>
                <input
                  type="text"
                  value={currVal}
                  onChange={(e) => setCurrVal(e.target.value)}
                  placeholder="e.g. 92% or Semester 3"
                  className="w-full rounded-xl border border-input bg-background px-3 py-2 text-xs font-semibold focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-foreground">Desired / Correct Value</label>
                <input
                  type="text"
                  value={proposedValue}
                  onChange={(e) => setProposedValue(e.target.value)}
                  placeholder="e.g. 95% or Semester 4"
                  className="w-full rounded-xl border border-input bg-background px-3 py-2 text-xs font-semibold focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-foreground">
                Description of Inaccuracy <span className="text-rose-500">*</span>
              </label>
              <textarea
                required
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain what is inaccurate and provide relevant details or dates..."
                className="w-full rounded-xl border border-input bg-background p-3 text-xs focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Direct supporting file upload */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-foreground flex items-center justify-between">
                <span>Supporting Document (Optional)</span>
                <span className="text-[11px] font-normal text-muted-foreground">PDF, PNG, JPG</span>
              </label>

              {uploadedDocName ? (
                <div className="flex items-center justify-between gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-700 font-bold">
                  <div className="flex items-center gap-2 truncate">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                    <span className="truncate">{uploadedDocName}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setUploadedDocId(null);
                      setUploadedDocName(null);
                    }}
                    className="text-muted-foreground hover:text-rose-600 cursor-pointer text-xs"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/80 bg-muted/20 p-4 cursor-pointer hover:bg-accent/50 transition-colors">
                  {uploading ? (
                    <span className="text-xs font-bold text-muted-foreground">Uploading document...</span>
                  ) : (
                    <>
                      <Upload className="h-6 w-6 text-muted-foreground mb-1" />
                      <span className="text-xs font-bold text-foreground">Click to upload document</span>
                      <span className="text-[10px] text-muted-foreground">Marksheet, hall ticket, official notice</span>
                    </>
                  )}
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                </label>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-border/60 pt-3 mt-4">
              <Button type="button" variant="outline" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                isLoading={submitMutation.isPending}
                disabled={!description.trim() || description.length < 10 || uploading}
              >
                Submit Request
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
