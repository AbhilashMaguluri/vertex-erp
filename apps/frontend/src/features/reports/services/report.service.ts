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
};
