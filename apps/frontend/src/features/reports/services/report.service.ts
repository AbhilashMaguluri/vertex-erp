import { api } from '@/shared/lib/axios';

export interface ReportRecord {
  id: string;
  report_type: string;
  generated_by_user_id: string;
  file_path: string;
  file_format: string;
  created_at: string;
}

export interface ReportGenerateData {
  report_type: string; // STUDENT, SEMESTER, DEPARTMENT, COUNSELLOR, ATTENDANCE, PERFORMANCE, BACKLOG
  file_format: string; // PDF, EXCEL, CSV
  scope_metadata?: Record<string, any>;
}

export const reportService = {
  generateReport: async (data: ReportGenerateData): Promise<ReportRecord> => {
    const res = await api.post<ReportRecord>('/reports/generate', data);
    return res.data;
  },

  getReportHistory: async (): Promise<ReportRecord[]> => {
    const res = await api.get<ReportRecord[]>('/reports/history');
    return res.data;
  },

  downloadReport: async (report: ReportRecord): Promise<void> => {
    const res = await api.get(`/reports/${report.id}/download`, { responseType: 'blob' });
    const disposition = res.headers['content-disposition'] as string | undefined;
    const match = disposition?.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] || `report_${report.report_type.toLowerCase()}.${report.file_format.toLowerCase()}`;

    const url = window.URL.createObjectURL(res.data as Blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
