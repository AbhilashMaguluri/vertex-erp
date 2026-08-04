import { api } from '@/shared/lib/axios';

/**
 * Membership Import — the administrator uploads a three-column Excel
 * (Start Roll, End Roll, Counselor Email) and the server derives everything.
 */

// --- Types ------------------------------------------------------------------

export interface PreviewSummary {
  total_students: number;
  existing_student_accounts: number;
  new_student_accounts: number;
  existing_counselor_accounts: number;
  missing_counselors: number;
  existing_memberships: number;
  new_memberships: number;
  warnings: number;
  errors: number;
}

export interface StudentPreviewRow {
  roll_number: string;
  email_used?: string | null;
  name?: string | null;
  status: string;
  action: string;
}

export interface CounselorPreviewRow {
  email: string;
  name?: string | null;
  status: string;
  action: string;
  student_count: number;
}

export interface MembershipPreviewRow {
  student_roll: string;
  student_name?: string | null;
  counselor_email: string;
  counselor_name?: string | null;
  status: string;
  action: string;
  error?: string | null;
}

export interface PreviewTables {
  students: StudentPreviewRow[];
  counselors: CounselorPreviewRow[];
  memberships: MembershipPreviewRow[];
}

export interface ValidationErrorRow {
  row: number;
  error: string;
  description: string;
  suggested_fix: string;
}

export interface MembershipImportPreview {
  batch_id: string;
  file_name: string;
  status: string;
  summary: PreviewSummary;
  tables: PreviewTables;
  validation_errors: ValidationErrorRow[];
  warnings: string[];
  errors: string[];
  parsed_row_count: number;
  expanded_student_count: number;
}

export interface MembershipImportConfiguration {
  department_id: string;
  semester_id: string;
  section_name: string;
  batch_year: number;
  academic_year_id?: string | null;
  study_year?: number | null;
  reassign_existing_students: boolean;
}

export interface MembershipImportProgress {
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

export interface MembershipImportResultRecord {
  record_type: string;
  identifier: string;
  display_name?: string | null;
  status: string;
  message?: string | null;
  source_row_number?: number | null;
}

export interface GeneratedStudentCredential {
  roll_number: string;
  full_name: string;
  username: string;
  email: string;
  temporary_password: string;
  counselor_email: string;
  status: string;
}

export interface MembershipImportSummary {
  batch_id: string;
  file_name: string;
  status: string;
  imported_by?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  total_rows: number;
  students_detected: number;
  students_created: number;
  students_reused: number;
  students_skipped: number;
  counselors_found: number;
  counselors_missing: number;
  memberships_created: number;
  memberships_updated: number;
  memberships_skipped: number;
  failed_records: number;
  warning_count: number;
  error_message?: string | null;
  credentials_available: boolean;
  credential_count: number;
  records: MembershipImportResultRecord[];
}

export interface MembershipImportHistoryItem {
  batch_id: string;
  file_name: string;
  status: string;
  imported_by?: string | null;
  created_at: string;
  completed_at?: string | null;
  students_created: number;
  students_reused: number;
  memberships_created: number;
  failed_records: number;
  credentials_available: boolean;
}

export interface MembershipImportHistory {
  items: MembershipImportHistoryItem[];
  total_imports: number;
  completed_imports: number;
  total_memberships_created: number;
  total_students_created: number;
  success_rate: number;
  last_import_at?: string | null;
}

// --- Helper -----------------------------------------------------------------

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

export const membershipImportService = {
  analyze: async (file: File): Promise<MembershipImportPreview> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<MembershipImportPreview>(
      '/admin/membership-imports/analyze',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return res.data;
  },

  getPreview: async (batchId: string): Promise<MembershipImportPreview> => {
    const res = await api.get<MembershipImportPreview>(
      `/admin/membership-imports/${batchId}/preview`,
    );
    return res.data;
  },

  execute: async (
    batchId: string,
    config: MembershipImportConfiguration,
  ): Promise<MembershipImportProgress> => {
    const res = await api.post<MembershipImportProgress>(
      `/admin/membership-imports/${batchId}/execute`,
      config,
    );
    return res.data;
  },

  getProgress: async (batchId: string): Promise<MembershipImportProgress> => {
    const res = await api.get<MembershipImportProgress>(
      `/admin/membership-imports/${batchId}/progress`,
    );
    return res.data;
  },

  getSummary: async (batchId: string): Promise<MembershipImportSummary> => {
    const res = await api.get<MembershipImportSummary>(
      `/admin/membership-imports/${batchId}`,
    );
    return res.data;
  },

  getCredentials: async (
    batchId: string,
    limit = 50,
  ): Promise<GeneratedStudentCredential[]> => {
    const res = await api.get<GeneratedStudentCredential[]>(
      `/admin/membership-imports/${batchId}/credentials`,
      { params: { limit } },
    );
    return res.data;
  },

  purgeCredentials: async (batchId: string): Promise<void> => {
    await api.delete(`/admin/membership-imports/${batchId}/credentials`);
  },

  getHistory: async (limit = 20): Promise<MembershipImportHistory> => {
    const res = await api.get<MembershipImportHistory>(
      '/admin/membership-imports',
      { params: { limit } },
    );
    return res.data;
  },

  downloadCredentials: (batchId: string) =>
    downloadBlob(
      `/admin/membership-imports/${batchId}/credentials.xlsx`,
      'membership_credentials.xlsx',
    ),

  downloadErrorReport: (batchId: string) =>
    downloadBlob(
      `/admin/membership-imports/${batchId}/errors.xlsx`,
      'Import_Errors.xlsx',
    ),

  downloadReport: (batchId: string) =>
    downloadBlob(
      `/admin/membership-imports/${batchId}/report.xlsx`,
      'membership_import_report.xlsx',
    ),

  downloadSampleTemplate: () =>
    downloadBlob(
      '/admin/membership-imports/sample-template.xlsx',
      'Membership_Import_Template.xlsx',
    ),
};
