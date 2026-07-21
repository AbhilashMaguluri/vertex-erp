import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportService, ReportRecord, ReportGenerateData } from '../services/report.service';
import { AppShell } from '@/shared/components/layout/AppShell';
import { PageHeader } from '@/shared/components/ui/PageHeader';
import { Breadcrumbs } from '@/shared/components/ui/Breadcrumbs';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/Card';
import { Badge } from '@/shared/components/ui/Badge';
import { Skeleton } from '@/shared/components/ui/Skeleton';
import { EmptyState } from '@/shared/components/ui/EmptyState';
import { FileCheck, Download, FileSpreadsheet, FileText, CheckCircle2 } from 'lucide-react';

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [reportType, setReportType] = React.useState('DEPARTMENT');
  const [fileFormat, setFileFormat] = React.useState('PDF');
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

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
    <AppShell userRole="HOD" userName="Dr. Suresh (HOD)">
      <Breadcrumbs items={[{ label: 'Reports Catalog' }]} />

      <PageHeader
        title="Accreditation-Ready Reports & Exports"
        subtitle="Generate institution-wide, department, counsellor, and student compliance reports (§26)"
      />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generator Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileCheck className="h-4 w-4 text-primary" /> Report Generator
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {successMsg && (
              <div className="flex items-center gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-xs font-medium text-emerald-800">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Report Category</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full h-9 rounded-md border bg-transparent px-3 text-xs"
              >
                <option value="DEPARTMENT">Department Compliance Report</option>
                <option value="COUNSELLOR">Counsellor Activity Report</option>
                <option value="ATTENDANCE">Attendance Defaulters Report</option>
                <option value="PERFORMANCE">Academic Performance Report</option>
                <option value="BACKLOG">Backlog Summary Report</option>
                <option value="SEMESTER">End of Semester Audit Report</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold">Export Format</label>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value="PDF"
                    checked={fileFormat === 'PDF'}
                    onChange={() => setFileFormat('PDF')}
                  />
                  PDF Document
                </label>

                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value="EXCEL"
                    checked={fileFormat === 'EXCEL'}
                    onChange={() => setFileFormat('EXCEL')}
                  />
                  Excel Workbook
                </label>

                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value="CSV"
                    checked={fileFormat === 'CSV'}
                    onChange={() => setFileFormat('CSV')}
                  />
                  CSV Data
                </label>
              </div>
            </div>

            <Button onClick={handleGenerate} className="w-full" disabled={generateMutation.isPending}>
              {generateMutation.isPending ? 'Generating Report...' : 'Generate Report'}
            </Button>
          </CardContent>
        </Card>

        {/* History Catalog */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-base font-semibold">Previously Generated Reports</h3>

          {isLoading ? (
            <Skeleton className="h-48" />
          ) : !reportHistory || reportHistory.length === 0 ? (
            <EmptyState
              icon={FileCheck}
              title="No Generated Reports"
              description="Use the generator on the left to create accreditation-ready reports."
            />
          ) : (
            <div className="space-y-3">
              {reportHistory.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg bg-card">
                  <div className="flex items-center gap-3">
                    {report.file_format === 'EXCEL' || report.file_format === 'CSV' ? (
                      <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                    ) : (
                      <FileText className="h-5 w-5 text-red-600" />
                    )}
                    <div>
                      <h4 className="text-sm font-semibold">{report.report_type} REPORT</h4>
                      <p className="text-xs text-muted-foreground">
                        Generated on {new Date(report.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{report.file_format}</Badge>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4 mr-1" /> Download
                    </Button>
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
