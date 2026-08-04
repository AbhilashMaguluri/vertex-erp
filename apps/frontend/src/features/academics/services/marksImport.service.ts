import { api } from '@/shared/lib/axios';

/**
 * Marks Import & Assessment Management API Service.
 */

// --- Interfaces -------------------------------------------------------------

export interface AssessmentComponent {
  key: string;
  label: string;
  max_marks: number;
}

export interface AssessmentTemplate {
  id: string;
  subject_id?: string | null;
  assessment_code: string;
  assessment_name: string;
  total_max_marks: number;
  components: AssessmentComponent[];
  description?: string | null;
}

export interface MarksPreviewSummary {
  subject_code?: string | null;
  subject_name?: string | null;
  assessment_code: string;
  assessment_name: string;
  total_max_marks: number;
  total_students_in_file: number;
  existing_students_found: number;
  missing_students: number;
  new_records: number;
  updates: number;
  skipped_records: number;
  warnings: number;
  errors: number;
}

export interface StudentMarksPreviewRow {
  roll_number: string;
  student_name?: string | null;
  question_breakdown: string;
  total_marks: number;
  max_marks: number;
  student_found: string;
  existing_marks: string;
  action: string;
  error?: string | null;
}

export interface MarksPreviewTables {
  records: StudentMarksPreviewRow[];
}

export interface MarksValidationErrorRow {
  row: number;
  roll_number: string;
  error: string;
  suggested_fix: string;
}

export interface MarksImportPreview {
  batch_id: string;
  file_name: string;
  status: string;
  summary: MarksPreviewSummary;
  tables: MarksPreviewTables;
  validation_errors: MarksValidationErrorRow[];
  warnings: string[];
  errors: string[];
  parsed_row_count: number;
}

export interface MarksImportConfiguration {
  academic_year_id?: string | null;
  semester_id: string;
  department_id?: string | null;
  section_id?: string | null;
  subject_id: string;
  assessment_code: string;
  allow_overwrite: boolean;
}

export interface MarksImportProgress {
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

export interface MarksImportResultRecord {
  record_type: string;
  identifier: string;
  display_name?: string | null;
  status: string;
  message?: string | null;
  source_row_number?: number | null;
}

export interface MarksImportSummary {
  batch_id: string;
  file_name: string;
  status: string;
  subject_code?: string | null;
  subject_name?: string | null;
  assessment_code: string;
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
  records: MarksImportResultRecord[];
}

export interface MarksImportHistoryItem {
  batch_id: string;
  file_name: string;
  subject_name?: string | null;
  assessment_code: string;
  status: string;
  imported_by?: string | null;
  created_at: string;
  completed_at?: string | null;
  records_created: number;
  records_updated: number;
  failed_records: number;
}

export interface MarksImportHistory {
  items: MarksImportHistoryItem[];
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

export const marksImportService = {
  // Assessment Templates
  getTemplates: async (subjectId?: string): Promise<AssessmentTemplate[]> => {
    const res = await api.get<AssessmentTemplate[]>('/admin/assessment-templates', {
      params: { subject_id: subjectId },
    });
    return res.data;
  },

  createTemplate: async (data: Partial<AssessmentTemplate>): Promise<AssessmentTemplate> => {
    const res = await api.post<AssessmentTemplate>('/admin/assessment-templates', data);
    return res.data;
  },

  updateTemplate: async (
    templateId: string,
    data: Partial<AssessmentTemplate>,
  ): Promise<AssessmentTemplate> => {
    const res = await api.put<AssessmentTemplate>(
      `/admin/assessment-templates/${templateId}`,
      data,
    );
    return res.data;
  },

  downloadDynamicTemplate: (assessmentCode: string, subjectId?: string) =>
    downloadBlob(
      `/admin/marks-imports/sample-template.xlsx?assessment_code=${encodeURIComponent(assessmentCode)}${subjectId ? `&subject_id=${encodeURIComponent(subjectId)}` : ''}`,
      `Marks_Template_${assessmentCode}.xlsx`,
    ),

  // Marks Import Workflow
  analyze: async (
    file: File,
    semesterId: string,
    subjectId: string,
    assessmentCode: string,
    academicYearId?: string,
    departmentId?: string,
    sectionId?: string,
  ): Promise<MarksImportPreview> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('semester_id', semesterId);
    formData.append('subject_id', subjectId);
    formData.append('assessment_code', assessmentCode);
    if (academicYearId) formData.append('academic_year_id', academicYearId);
    if (departmentId) formData.append('department_id', departmentId);
    if (sectionId) formData.append('section_id', sectionId);

    const res = await api.post<MarksImportPreview>(
      '/admin/marks-imports/analyze',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return res.data;
  },

  getPreview: async (batchId: string): Promise<MarksImportPreview> => {
    const res = await api.get<MarksImportPreview>(
      `/admin/marks-imports/${batchId}/preview`,
    );
    return res.data;
  },

  execute: async (
    batchId: string,
    config: MarksImportConfiguration,
  ): Promise<MarksImportProgress> => {
    const res = await api.post<MarksImportProgress>(
      `/admin/marks-imports/${batchId}/execute`,
      config,
    );
    return res.data;
  },

  getProgress: async (batchId: string): Promise<MarksImportProgress> => {
    const res = await api.get<MarksImportProgress>(
      `/admin/marks-imports/${batchId}/progress`,
    );
    return res.data;
  },

  getSummary: async (batchId: string): Promise<MarksImportSummary> => {
    const res = await api.get<MarksImportSummary>(
      `/admin/marks-imports/${batchId}`,
    );
    return res.data;
  },

  getHistory: async (limit = 20): Promise<MarksImportHistory> => {
    const res = await api.get<MarksImportHistory>(
      '/admin/marks-imports',
      { params: { limit } },
    );
    return res.data;
  },

  downloadErrorReport: (batchId: string) =>
    downloadBlob(
      `/admin/marks-imports/${batchId}/errors.xlsx`,
      'Marks_Import_Errors.xlsx',
    ),

  downloadReport: (batchId: string) =>
    downloadBlob(
      `/admin/marks-imports/${batchId}/report.xlsx`,
      'marks_import_report.xlsx',
    ),
};
