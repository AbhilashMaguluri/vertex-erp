import * as React from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  X,
  Users,
  Link2,
} from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { cn } from '@/shared/utils/cn';
import { membershipImportService } from '../../services/membershipImport.service';

const ACCEPTED = '.xlsx,.xlsm,.xls,.csv';
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm', '.xls', '.csv'];

const WHAT_IT_READS = [
  {
    icon: FileSpreadsheet,
    title: 'Three simple columns',
    body: 'Start Roll Number, End Roll Number, and Counselor Email — nothing else needed.',
  },
  {
    icon: Users,
    title: 'Automatic expansion',
    body: 'Roll number ranges like 23BQ1A5401 → 23BQ1A5410 are expanded into individual students automatically.',
  },
  {
    icon: Link2,
    title: 'Smart matching',
    body: 'Existing students and counselors are matched by email. Missing counselors are flagged — never created automatically.',
  },
];

interface MembershipUploadStepProps {
  onAnalyzed: (batchId: string) => void;
}

export function MembershipUploadStep({ onAnalyzed }: MembershipUploadStepProps) {
  const [file, setFile] = React.useState<File | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type. Upload one of: ${ACCEPTED_EXTENSIONS.join(', ')}`;
    }
    if (f.size > 12 * 1024 * 1024) {
      return 'File is too large (max 12 MB).';
    }
    return null;
  };

  const handleFileSelect = (f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
  };

  const analyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const preview = await membershipImportService.analyze(file);
      onAnalyzed(preview.batch_id);
    } catch (err: any) {
      setError(
        err?.response?.data?.error?.message ??
        err?.response?.data?.detail ??
        'Analysis failed. Check the file format and try again.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      {/* Upload zone */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-primary" />
            Upload Membership File
          </CardTitle>
          <CardDescription>
            A three-column Excel: Start Roll Number, End Roll Number, Counselor Email
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className={cn(
              'flex min-h-[200px] cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-8 transition-all duration-200',
              isDragging
                ? 'border-primary bg-primary/5'
                : file
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-border hover:border-primary/50 hover:bg-primary/5',
            )}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFileSelect(f);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED}
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFileSelect(f);
              }}
            />
            {file ? (
              <>
                <div className="flex items-center gap-3 rounded-xl bg-emerald-500/10 px-4 py-3">
                  <FileSpreadsheet className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                  <div>
                    <p className="text-sm font-bold text-foreground">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <button
                    className="ml-4 rounded-full p-1 hover:bg-foreground/10"
                    onClick={(e) => { e.stopPropagation(); setFile(null); setError(null); }}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <Button onClick={(e) => { e.stopPropagation(); analyze(); }} disabled={isAnalyzing} size="lg">
                  {isAnalyzing ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Analyzing…
                    </>
                  ) : (
                    'Analyze & Preview'
                  )}
                </Button>
              </>
            ) : (
              <>
                <UploadCloud className="h-10 w-10 text-muted-foreground" />
                <div className="text-center">
                  <p className="font-semibold text-foreground">
                    Drop your file here or click to browse
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Excel (.xlsx, .xls) or CSV — max 12 MB
                  </p>
                </div>
              </>
            )}
          </div>

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <p className="text-xs text-rose-700 dark:text-rose-300">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info panel */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Expected Format</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {WHAT_IT_READS.map((item) => (
            <div key={item.title} className="flex gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <item.icon className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{item.title}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{item.body}</p>
              </div>
            </div>
          ))}

          <div className="rounded-lg border border-border/50 bg-muted/30 p-3">
            <p className="mb-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Example
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="px-2 py-1.5 text-left font-semibold">Start Roll</th>
                    <th className="px-2 py-1.5 text-left font-semibold">End Roll</th>
                    <th className="px-2 py-1.5 text-left font-semibold">Counselor Email</th>
                  </tr>
                </thead>
                <tbody className="text-muted-foreground">
                  <tr><td className="px-2 py-1">23BQ1A5401</td><td className="px-2 py-1">23BQ1A5410</td><td className="px-2 py-1">ravindra@vvit.net</td></tr>
                  <tr><td className="px-2 py-1">23BQ1A5411</td><td className="px-2 py-1">23BQ1A5420</td><td className="px-2 py-1">srinivas@vvit.net</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
