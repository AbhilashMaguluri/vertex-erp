import { api } from '@/shared/lib/axios';

/**
 * Attendance Import — upload bulk attendance records for today or past dates
 * using a clean two-column format (Student Roll Number, Attendance Status).
 */

// --- Interfaces -------------------------------------------------------------

export interface AttendancePreviewSummary {
  attendance_date: string;
  mode: 'TODAY' | 'PAST';
  subject_code?: string | null;
  subject_name?: string | null;
  total_students_in_file: number;
  existing_students_found: number;
  missing_students: number;
  new_attendance_records: number;
  attendance_updates: number;
  skipped_records: number;
  warnings: number;
  errors: number;
}

export interface StudentAttendancePreviewRow {
  roll_number: string;
  student_name?: string | null;
  status: string;
  student_found: string;
  existing_attendance: string;
  action: string;
  error?: string | null;
}

export interface AttendancePreviewTables {
  records: StudentAttendancePreviewRow[];
}

export interface AttendanceValidationErrorRow {
  row: number;
  roll_number: string;
  error: string;
  suggested_fix: string;
}

export interface AttendanceImportPreview {
  batch_id: string;
  file_name: string;
  status: string;
  summary: AttendancePreviewSummary;
  tables: AttendancePreviewTables;
  validation_errors: AttendanceValidationErrorRow[];
  warnings: string[];
  errors: string[];
  parsed_row_count: number;
}

export interface AttendanceImportConfiguration {
  mode: 'TODAY' | 'PAST';
  attendance_date: string;
  subject_id: string;
  department_id?: string | null;
  section_id?: string | null;
  allow_overwrite: boolean;
}

export interface AttendanceImportProgress {
  batch_id: string;
  status: string;
  phase: string;
  phase_label: string;
  percent: number;
  processed: number;
  total: number;
  message?: string | null;
  error?: string | null;
}

export interface AttendanceImportResultRecord {
  record_type: string;
  identifier: string;
  display_name?: string | null;
  status: string;
  message?: string | null;
  source_row_number?: number | null;
}

export interface AttendanceImportSummary {
  batch_id: string;
  file_name: string;
  status: string;
  mode: string;
  attendance_date: string;
  subject_code?: string | null;
  subject_name?: string | null;
  imported_by?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  total_rows: number;
  students_detected: number;
  students_found: number;
  missing_students: number;
  records_created: number;
  records_updated: number;
  records_skipped: number;
  failed_records: number;
  warning_count: number;
  error_message?: string | null;
  records: AttendanceImportResultRecord[];
}

export interface AttendanceImportHistoryItem {
  batch_id: string;
  file_name: string;
  mode: string;
  attendance_date: string;
  subject_name?: string | null;
  status: string;
  imported_by?: string | null;
  created_at: string;
  completed_at?: string | null;
  records_created: number;
  records_updated: number;
  failed_records: number;
}

export interface AttendanceImportHistory {
  items: AttendanceImportHistoryItem[];
  total_imports: number;
  completed_imports: number;
  total_records_created: number;
  total_records_updated: number;
  success_rate: number;
  last_import_at?: string | null;
}

// --- Helper Download --------------------------------------------------------

async function downloadBlob(url: string, fallbackName: string): Promise<void> {
  const res = await api.get(url, { responseType: 'blob' });
  const disposition = String(res.headers?.['content-disposition'] ?? '');
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] ?? fallbackName;
  const href = URL.createObjectURL(res.data as Blob);
  const anchor = document.createElement('a');
  anchor.href = href;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(href), 0);
}

// --- Service ----------------------------------------------------------------

export const attendanceImportService = {
  analyze: async (
    file: File,
    mode: 'TODAY' | 'PAST',
    attendanceDate?: string,
    subjectId?: string,
    departmentId?: string,
    sectionId?: string,
  ): Promise<AttendanceImportPreview> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    if (attendanceDate) formData.append('attendance_date', attendanceDate);
    if (subjectId) formData.append('subject_id', subjectId);
    if (departmentId) formData.append('department_id', departmentId);
    if (sectionId) formData.append('section_id', sectionId);

    const res = await api.post<AttendanceImportPreview>(
      '/admin/attendance-imports/analyze',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return res.data;
  },

  getPreview: async (batchId: string): Promise<AttendanceImportPreview> => {
    const res = await api.get<AttendanceImportPreview>(
      `/admin/attendance-imports/${batchId}/preview`,
    );
    return res.data;
  },

  execute: async (
    batchId: string,
    config: AttendanceImportConfiguration,
  ): Promise<AttendanceImportProgress> => {
    const res = await api.post<AttendanceImportProgress>(
      `/admin/attendance-imports/${batchId}/execute`,
      config,
    );
    return res.data;
  },

  getProgress: async (batchId: string): Promise<AttendanceImportProgress> => {
    const res = await api.get<AttendanceImportProgress>(
      `/admin/attendance-imports/${batchId}/progress`,
    );
    return res.data;
  },

  getSummary: async (batchId: string): Promise<AttendanceImportSummary> => {
    const res = await api.get<AttendanceImportSummary>(
      `/admin/attendance-imports/${batchId}`,
    );
    return res.data;
  },

  getHistory: async (limit = 20): Promise<AttendanceImportHistory> => {
    const res = await api.get<AttendanceImportHistory>(
      '/admin/attendance-imports',
      { params: { limit } },
    );
    return res.data;
  },

  downloadErrorReport: (batchId: string) =>
    downloadBlob(
      `/admin/attendance-imports/${batchId}/errors.xlsx`,
      'Attendance_Import_Errors.xlsx',
    ),

  downloadReport: (batchId: string) =>
    downloadBlob(
      `/admin/attendance-imports/${batchId}/report.xlsx`,
      'attendance_import_report.xlsx',
    ),

  downloadSampleTemplate: () =>
    downloadBlob(
      '/admin/attendance-imports/sample-template.xlsx',
      'Attendance_Import_Template.xlsx',
    ),
};
