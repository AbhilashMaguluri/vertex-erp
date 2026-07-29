import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportService, ReportRecord, ReportGenerateData } from '../services/report.service';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { FileCheck, Download, FileSpreadsheet, FileText, CheckCircle2, Sparkles } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [reportType, setReportType] = React.useState('DEPARTMENT');
  const [fileFormat, setFileFormat] = React.useState('PDF');
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);
  const [downloadingId, setDownloadingId] = React.useState<string | null>(null);
  const [downloadError, setDownloadError] = React.useState<string | null>(null);

  const handleDownload = async (report: ReportRecord) => {
    setDownloadError(null);
    setDownloadingId(report.id);
    try {
      await reportService.downloadReport(report);
    } catch (err: any) {
      setDownloadError(err?.response?.data?.error?.message || 'Failed to download report.');
    } finally {
      setDownloadingId(null);
    }
  };

  const { data: reportHistory, isLoading } = useQuery<ReportRecord[]>({
    queryKey: ['reports', 'history'],
    queryFn: reportService.getReportHistory,
  });

  const generateMutation = useMutation({
    mutationFn: (data: ReportGenerateData) => reportService.generateReport(data),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'history'] });
      setSuccessMsg(`Report (${res.report_type}) generated successfully as ${res.file_format}.`);
      setTimeout(() => setSuccessMsg(null), 4000);
    },
  });

  const handleGenerate = () => {
    generateMutation.mutate({
      report_type: reportType,
      file_format: fileFormat,
    });
  };

  return (
    <>
      <Breadcrumbs items={[{ label: 'Reports Catalog' }]} />

      <PageHeader
        title="Accreditation & Analytics Reports"
        subtitle="Generate institution-wide compliance exports, department analytics, and audit summaries"
      />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generator Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Report Generator
            </CardTitle>
            <CardDescription>Select dataset parameters and format</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {successMsg && (
              <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Report Category</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full h-10 rounded-lg border border-input bg-background px-3 text-xs font-semibold focus:ring-2 focus:ring-ring"
              >
                <option value="DEPARTMENT">Department Compliance Report</option>
                <option value="COUNSELLOR">Counsellor Activity Summary</option>
                <option value="ATTENDANCE">Attendance Defaulters Roster</option>
                <option value="PERFORMANCE">Academic Performance Analysis</option>
                <option value="BACKLOG">Backlog Audit Summary</option>
                <option value="SEMESTER">End-of-Semester Institutional Audit</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Export Format</label>
              <div className="grid grid-cols-3 gap-2 pt-1">
                {(['PDF', 'EXCEL', 'CSV'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => setFileFormat(fmt)}
                    className={cn(
                      'py-2 px-3 rounded-lg border text-xs font-bold transition-all cursor-pointer select-none',
                      fileFormat === fmt
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border bg-background text-muted-foreground hover:bg-accent'
                    )}
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            </div>

            <Button onClick={handleGenerate} className="w-full" isLoading={generateMutation.isPending} size="lg">
              Generate & Publish Report
            </Button>
          </CardContent>
        </Card>

        {/* History Catalog */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-bold text-foreground tracking-tight">Generated Archive Catalog</h3>

          {downloadError && (
            <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs font-medium text-rose-600 dark:text-rose-400">
              <span>{downloadError}</span>
            </div>
          )}

          {isLoading ? (
            <Skeleton className="h-48 rounded-xl" />
          ) : !reportHistory || reportHistory.length === 0 ? (
            <EmptyState
              icon={FileCheck}
              title="No Generated Reports"
              description="Use the generator on the left to create accreditation-ready PDF or Excel exports."
            />
          ) : (
            <div className="space-y-3">
              {reportHistory.map((report) => (
                <Card key={report.id}>
                  <CardContent className="p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                      {report.file_format === 'EXCEL' || report.file_format === 'CSV' ? (
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 font-bold">
                          <FileSpreadsheet className="h-5 w-5" />
                        </div>
                      ) : (
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-600 font-bold">
                          <FileText className="h-5 w-5" />
                        </div>
                      )}
                      <div>
                        <h4 className="text-xs font-bold text-foreground">{report.report_type} REPORT</h4>
                        <p className="text-[11px] font-mono text-muted-foreground mt-0.5">
                          Generated {new Date(report.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{report.file_format}</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(report)}
                        isLoading={downloadingId === report.id}
                      >
                        <Download className="h-4 w-4 mr-1" /> Export
                      </Button>
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
