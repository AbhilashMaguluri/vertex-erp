import { api } from '@/shared/lib/axios';

/**
 * Office Import — the administrator uploads the allotment sheet the college
 * office already keeps and the server derives everything else. Nothing in this
 * contract carries an identifier the office would have to look up.
 */

export interface DetectedColumn {
  field: string;
  source_header: string;
  label: string;
}

export interface DetectedRange {
  row_number: number;
  raw_text: string;
  description: string;
  student_count: number;
  counsellor_name?: string | null;
  counsellor_phone?: string | null;
  first_roll?: string | null;
  last_roll?: string | null;
  warnings: string[];
  errors: string[];
}

export interface DetectedCounsellor {
  key: string;
  name_as_written: string;
  display_name: string;
  phone?: string | null;
  email?: string | null;
  proposed_username?: string | null;
  student_count: number;
  status: 'NEW' | 'EXISTING';
  existing_user_id?: string | null;
  matched_on?: string | null;
  rows: number[];
}

export interface DuplicateStudent {
  roll_number: string;
  reason: string;
  existing_name?: string | null;
  row_numbers: number[];
}

export type SuggestionSource = 'FILE' | 'DERIVED' | 'CURRENT' | 'NONE';
export type SuggestionConfidence = 'HIGH' | 'MEDIUM' | 'NONE';

export interface FieldSuggestion {
  field: string;
  label: string;
  required: boolean;
  source: SuggestionSource;
  detected_value?: string | null;
  detected_id?: string | null;
  confidence: SuggestionConfidence;
  note?: string | null;
}

export interface ImportPreview {
  batch_id: string;
  file_name: string;
  sheet_name: string;
  header_row_number: number;
  status: string;
  detected_columns: DetectedColumn[];
  ignored_columns: string[];
  total_rows: number;
  valid_rows: number;
  students_detected: number;
  counsellors_detected: number;
  new_counsellors: number;
  existing_counsellors: number;
  duplicate_students: number;
  importable_students: number;
  ranges: DetectedRange[];
  counsellors: DetectedCounsellor[];
  duplicates: DuplicateStudent[];
  suggestions: FieldSuggestion[];
  warnings: string[];
  errors: string[];
  sample_roll_numbers: string[];
}

export interface ImportConfiguration {
  department_id: string;
  semester_id: string;
  section_name: string;
  batch_year: number;
  academic_year_id?: string | null;
  study_year?: number | null;
  reassign_existing_students: boolean;
}

export interface ImportProgress {
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

export interface ImportRecordResult {
  record_type: 'STUDENT' | 'COUNSELLOR';
  identifier: string;
  display_name?: string | null;
  status: 'CREATED' | 'REUSED' | 'SKIPPED' | 'FAILED';
  message?: string | null;
  source_row_number?: number | null;
}

export interface GeneratedCredential {
  record_type: 'STUDENT' | 'COUNSELLOR';
  identifier: string;
  full_name: string;
  username: string;
  email: string;
  temporary_password: string;
  counsellor?: string | null;
  status: string;
}

export interface ImportSummary {
  batch_id: string;
  file_name: string;
  status: string;
  imported_by?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  total_rows: number;
  students_detected: number;
  counsellors_detected: number;
  students_created: number;
  students_skipped: number;
  counsellors_created: number;
  counsellors_reused: number;
  assignments_created: number;
  failed_records: number;
  warning_count: number;
  error_message?: string | null;
  configuration?: Record<string, unknown> | null;
  credentials_available: boolean;
  credential_count: number;
  records: ImportRecordResult[];
}

export interface ImportHistoryItem {
  batch_id: string;
  file_name: string;
  status: string;
  imported_by?: string | null;
  created_at: string;
  completed_at?: string | null;
  students_created: number;
  counsellors_created: number;
  students_skipped: number;
  failed_records: number;
  credentials_available: boolean;
}

export interface ImportHistory {
  items: ImportHistoryItem[];
  total_imports: number;
  completed_imports: number;
  total_students_created: number;
  total_counsellors_created: number;
  success_rate: number;
  last_import_at?: string | null;
}

/** Trigger a browser download for a binary endpoint, preserving the filename. */
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
  // Revoked on the next tick: revoking synchronously can cancel the download
  // in Safari before it has read the object URL.
  setTimeout(() => URL.revokeObjectURL(href), 0);
}

export const officeImportService = {
  analyze: async (file: File): Promise<ImportPreview> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<ImportPreview>('/admin/imports/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  getPreview: async (batchId: string): Promise<ImportPreview> => {
    const res = await api.get<ImportPreview>(`/admin/imports/${batchId}/preview`);
    return res.data;
  },

  execute: async (batchId: string, config: ImportConfiguration): Promise<ImportProgress> => {
    const res = await api.post<ImportProgress>(`/admin/imports/${batchId}/execute`, config);
    return res.data;
  },

  getProgress: async (batchId: string): Promise<ImportProgress> => {
    const res = await api.get<ImportProgress>(`/admin/imports/${batchId}/progress`);
    return res.data;
  },

  getSummary: async (batchId: string): Promise<ImportSummary> => {
    const res = await api.get<ImportSummary>(`/admin/imports/${batchId}`);
    return res.data;
  },

  getCredentials: async (batchId: string, limit = 50): Promise<GeneratedCredential[]> => {
    const res = await api.get<GeneratedCredential[]>(`/admin/imports/${batchId}/credentials`, {
      params: { limit },
    });
    return res.data;
  },

  purgeCredentials: async (batchId: string): Promise<void> => {
    await api.delete(`/admin/imports/${batchId}/credentials`);
  },

  getHistory: async (limit = 20): Promise<ImportHistory> => {
    const res = await api.get<ImportHistory>('/admin/imports', { params: { limit } });
    return res.data;
  },

  downloadCredentials: (batchId: string) =>
    downloadBlob(`/admin/imports/${batchId}/credentials.xlsx`, 'scms_credentials.xlsx'),

  downloadReportExcel: (batchId: string) =>
    downloadBlob(`/admin/imports/${batchId}/report.xlsx`, 'scms_import_report.xlsx'),

  downloadReportPdf: (batchId: string) =>
    downloadBlob(`/admin/imports/${batchId}/report.pdf`, 'scms_import_report.pdf'),

  downloadSampleTemplate: () =>
    downloadBlob('/admin/imports/sample-template.xlsx', 'SCMS_Office_Import_Template.xlsx'),
};
