import { api } from '@/shared/lib/axios';

export interface StudentProfile {
  id: string;
  user_id: string;
  roll_number: string;
  registration_number: string;
  full_name: string;
  email: string;
  phone?: string;
  date_of_birth: string;
  batch_year: number;
  status: string;
  risk_level: string;
  department_id: string;
  department_name?: string;
  current_semester_id?: string;
  counsellor_name?: string;
  father_name?: string;
  father_phone?: string;
  mother_name?: string;
  mother_phone?: string;
  guardian_name?: string;
  guardian_phone?: string;
  created_at: string;
}

export interface OverviewStat {
  title: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
}

export interface Student360Data {
  profile: StudentProfile;
  stats: OverviewStat[];
  attention_items: string[];
  recent_events: any[];
}

export interface RosterStudent {
  id: string;
  roll_number: string;
  full_name: string;
}

/** One row of the counsellor's Assigned Students table. Every metric is
 *  nullable — a newly imported student legitimately has no attendance, marks
 *  or counselling history yet, and "no data" must not render as 0. */
export interface CaseloadStudent {
  id: string;
  roll_number: string;
  registration_number: string;
  full_name: string;
  email: string;
  phone?: string | null;
  gender?: string | null;
  photo_url?: string | null;
  study_year?: number | null;
  section_id?: string | null;
  section_name?: string | null;
  semester_id?: string | null;
  semester_name?: string | null;
  batch_year: number;
  department_id: string;
  department_name?: string | null;
  department_code?: string | null;
  attendance_percentage?: number | null;
  total_classes?: number | null;
  attended_classes?: number | null;
  sgpa?: number | null;
  cgpa?: number | null;
  active_backlogs: number;
  risk_level: string;
  status: string;
  last_session_date?: string | null;
  session_count: number;
  counsellor_id?: string | null;
  counsellor_name?: string | null;
  attendance_below_threshold: boolean;
}

export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface Paginated<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface CaseloadFilters {
  search?: string;
  year?: number;
  section_id?: string;
  semester_id?: string;
  department_id?: string;
  batch_year?: number;
  risk_level?: string;
  status?: string;
  min_attendance?: number;
  max_attendance?: number;
  min_cgpa?: number;
  max_cgpa?: number;
  has_backlogs?: boolean;
  counsellor_id?: string;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}

export interface FacetOption {
  id: string;
  label: string;
}

export interface CaseloadFacets {
  years: number[];
  sections: FacetOption[];
  semesters: FacetOption[];
  departments: FacetOption[];
  batch_years: number[];
  risk_levels: string[];
  statuses: string[];
}

export interface PendingActionItem {
  id: string;
  description: string;
  due_date: string;
  status: string;
  is_overdue: boolean;
  session_id: string;
  session_date: string;
}

/** Auto-populated header for the session recorder — the replacement for the
 *  old "type a Student ID" field. */
export interface SessionContext {
  student_id: string;
  roll_number: string;
  full_name: string;
  email: string;
  department_name?: string | null;
  section_name?: string | null;
  study_year?: number | null;
  semester_id?: string | null;
  semester_name?: string | null;
  attendance_percentage?: number | null;
  cgpa?: number | null;
  sgpa?: number | null;
  active_backlogs: number;
  risk_level: string;
  last_session_date?: string | null;
  last_session_summary?: string | null;
  last_session_type?: string | null;
  total_sessions: number;
  pending_action_items: PendingActionItem[];
  attention_items: string[];
}

/** Strips undefined/empty values so cleared filters don't go out as
 *  `?risk_level=` and get rejected by the API's validators. */
function cleanParams(filters: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== '')
  );
}

export interface AcademicCorrectionLog {
  id: string;
  actor_id: string;
  actor_name?: string;
  action: string;
  from_status?: string;
  to_status: string;
  remarks?: string;
  document_id?: string;
  created_at: string;
}

export interface AcademicCorrection {
  id: string;
  student_id: string;
  student_name?: string;
  student_roll?: string;
  counsellor_id?: string;
  counsellor_name?: string;
  section_name: string;
  current_value?: string;
  proposed_value?: string;
  description: string;
  document_id?: string;
  document_name?: string;
  document_url?: string;
  status: 'DRAFT' | 'SUBMITTED' | 'ASSIGNED' | 'UNDER_REVIEW' | 'NEED_MORE_INFO' | 'APPROVED' | 'REJECTED';
  counsellor_remarks?: string;
  reviewed_by_user_id?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at?: string;
  logs: AcademicCorrectionLog[];
}

export interface AcademicCorrectionCreate {
  section_name: string;
  current_value?: string;
  proposed_value?: string;
  description: string;
  document_id?: string;
}

export interface AcademicCorrectionReview {
  status: 'APPROVED' | 'REJECTED' | 'NEED_MORE_INFO' | 'UNDER_REVIEW';
  remarks?: string;
}

export interface AcademicCorrectionClarification {
  remarks?: string;
  document_id?: string;
}

export const studentService = {
  getStudent360: async (studentId: string): Promise<Student360Data> => {
    const res = await api.get<Student360Data>(`/students/${studentId}/workspace`);
    return res.data;
  },

  getMyWorkspace: async (): Promise<Student360Data> => {
    const res = await api.get<Student360Data>('/students/me/workspace');
    return res.data;
  },

  getSectionRoster: async (sectionId: string, semesterId: string): Promise<RosterStudent[]> => {
    const res = await api.get<RosterStudent[]>('/students/roster', {
      params: { section_id: sectionId, semester_id: semesterId },
    });
    return res.data;
  },

  getCaseload: async (filters: CaseloadFilters = {}): Promise<Paginated<CaseloadStudent>> => {
    const res = await api.get<Paginated<CaseloadStudent>>('/students/caseload', {
      params: cleanParams(filters as Record<string, unknown>),
    });
    return res.data;
  },

  getCaseloadFacets: async (): Promise<CaseloadFacets> => {
    const res = await api.get<CaseloadFacets>('/students/caseload/facets');
    return res.data;
  },

  getSessionContext: async (studentId: string): Promise<SessionContext> => {
    const res = await api.get<SessionContext>(`/students/${studentId}/session-context`);
    return res.data;
  },

  updateRiskFlag: async (studentId: string, risk_level: string, reason: string): Promise<StudentProfile> => {
    const res = await api.patch<StudentProfile>(`/students/${studentId}/risk`, {
      risk_level,
      reason,
    });
    return res.data;
  },

  // Academic Correction Requests
  createCorrectionRequest: async (data: AcademicCorrectionCreate): Promise<AcademicCorrection> => {
    const res = await api.post<AcademicCorrection>('/students/me/academic-corrections', data);
    return res.data;
  },

  getMyCorrectionRequests: async (): Promise<AcademicCorrection[]> => {
    const res = await api.get<AcademicCorrection[]>('/students/me/academic-corrections');
    return res.data;
  },

  getCaseloadCorrectionRequests: async (counsellorId?: string): Promise<AcademicCorrection[]> => {
    const res = await api.get<AcademicCorrection[]>('/students/academic-corrections/caseload', {
      params: counsellorId ? { counsellor_id: counsellorId } : undefined,
    });
    return res.data;
  },

  getCorrectionRequest: async (requestId: string): Promise<AcademicCorrection> => {
    const res = await api.get<AcademicCorrection>(`/students/academic-corrections/${requestId}`);
    return res.data;
  },

  reviewCorrectionRequest: async (requestId: string, data: AcademicCorrectionReview): Promise<AcademicCorrection> => {
    const res = await api.patch<AcademicCorrection>(`/students/academic-corrections/${requestId}/review`, data);
    return res.data;
  },

  submitCorrectionClarification: async (requestId: string, data: AcademicCorrectionClarification): Promise<AcademicCorrection> => {
    const res = await api.post<AcademicCorrection>(`/students/academic-corrections/${requestId}/clarification`, data);
    return res.data;
  },
};

