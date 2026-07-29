import * as React from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  Sparkles,
  AlertCircle,
  X,
  Table2,
  Users,
  Wand2,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { cn } from '@/shared/utils/cn';
import { officeImportService } from '../../services/import.service';

const ACCEPTED = '.xlsx,.xlsm,.xls,.csv';
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm', '.xls', '.csv'];

const WHAT_IT_READS = [
  {
    icon: Table2,
    title: 'Roll number ranges',
    body: '“23BQ1A5401 to 23BQ1A5410”, “23BQ1A5401-5410”, “23BQ1A5401 upto 5410” and comma-separated lists are all expanded into individual students.',
  },
  {
    icon: Users,
    title: 'Counsellor allotment',
    body: 'The counsellor name and mobile on each row. Existing staff accounts are reused; only genuinely new ones are created.',
  },
  {
    icon: Wand2,
    title: 'Everything else it can',
    body: 'Department, branch, section, semester, batch and academic year — from the sheet where present, from the roll number where not. Anything still missing is asked for once.',
  },
];

interface UploadStepProps {
  onAnalyzed: (batchId: string) => void;
}

export function UploadStep({ onAnalyzed }: UploadStepProps) {
  const [file, setFile] = React.useState<File | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const acceptFile = (candidate: File | null | undefined) => {
    if (!candidate) return;
    const name = candidate.name.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
      setError(`“${candidate.name}” is not a spreadsheet. Upload an ${ACCEPTED_EXTENSIONS.join(', ')} file.`);
      setFile(null);
      return;
    }
    setError(null);
    setFile(candidate);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const preview = await officeImportService.analyze(file);
      onAnalyzed(preview.batch_id);
    } catch (err: any) {
      setError(
        err?.response?.data?.error?.message ??
          'The file could not be read. Check that it is the allotment sheet and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-primary" />
            Upload the office file
          </CardTitle>
          <CardDescription>
            Upload the allotment sheet exactly as the office sent it. Nothing needs editing, renaming or
            converting first.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              acceptFile(e.dataTransfer.files?.[0]);
            }}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                inputRef.current?.click();
              }
            }}
            role="button"
            tabIndex={0}
            aria-label="Drag and drop the office file here, or browse for it"
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-all duration-200 focus-ring',
              isDragging
                ? 'border-primary bg-primary/10 scale-[1.01]'
                : 'border-border/80 bg-background/40 hover:border-primary/60 hover:bg-accent/40'
            )}
          >
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary ring-8 ring-primary/5">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-foreground">
              {isDragging ? 'Drop the file to begin' : 'Drag & drop your Excel or CSV file'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              or <span className="font-semibold text-primary underline underline-offset-2">browse</span> for it
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
              {ACCEPTED_EXTENSIONS.map((ext) => (
                <Badge key={ext} variant="secondary" className="font-mono text-[10px]">
                  {ext}
                </Badge>
              ))}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED}
              className="hidden"
              onChange={(e) => acceptFile(e.target.files?.[0])}
            />
          </div>

          {file && (
            <div className="flex items-center gap-3 rounded-xl border border-border/80 bg-card p-3.5 shadow-xs">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
                <FileSpreadsheet className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-foreground">{file.name}</p>
                <p className="text-[11px] font-medium text-muted-foreground">
                  {(file.size / 1024).toFixed(0)} KB · ready to analyse
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  setError(null);
                  if (inputRef.current) inputRef.current.value = '';
                }}
                aria-label="Remove the selected file"
                className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <p className="text-xs font-medium leading-relaxed text-rose-700 dark:text-rose-300">{error}</p>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button size="lg" onClick={handleAnalyze} disabled={!file} isLoading={isAnalyzing}>
              <Sparkles className="mr-1.5 h-4 w-4" />
              {isAnalyzing ? 'Reading the file…' : 'Analyse file'}
            </Button>
            <Button variant="outline" size="lg" onClick={() => officeImportService.downloadSampleTemplate()}>
              <Download className="mr-1.5 h-4 w-4" />
              Sample office template
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">What the importer reads</CardTitle>
          <CardDescription>
            Detection is automatic — the header row is found even when the sheet has a college name and a title
            above it, and S.No is ignored.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {WHAT_IT_READS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 text-primary">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-foreground">{title}</p>
                <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">{body}</p>
              </div>
            </div>
          ))}
          <p className="rounded-xl border border-border/60 bg-muted/40 p-3 text-[11px] leading-relaxed font-medium text-muted-foreground">
            Nothing is written to the system until you confirm the plan on the following steps.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
