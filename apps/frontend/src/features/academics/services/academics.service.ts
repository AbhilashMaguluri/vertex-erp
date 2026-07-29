import { api } from '@/shared/lib/axios';

export interface StudentMarkItem {
  student_id: string;
  marks_obtained: number;
  max_marks: number;
}

export interface BulkMarksCreateData {
  subject_id: string;
  semester_id: string;
  assessment_type: string;
  records: StudentMarkItem[];
}

export interface MarkRecord {
  id: string;
  student_id: string;
  subject_id: string;
  semester_id: string;
  assessment_type: string;
  marks_obtained: number;
  max_marks: number;
  recorded_by: string;
  created_at: string;
}

export interface BacklogItem {
  id: string;
  student_id: string;
  subject_id: string;
  subject_code?: string;
  subject_name?: string;
  semester_id: string;
  status: string;
  cleared_at_semester_id?: string;
  cleared_date?: string;
  created_at: string;
}

export interface SubjectResultRow {
  subject_id: string;
  subject_code: string;
  subject_name: string;
  credits: number;
  mid_1?: number | null;
  mid_2?: number | null;
  internal?: number | null;
  external?: number | null;
  total_obtained?: number | null;
  total_max?: number | null;
  percentage?: number | null;
  grade?: string | null;
  result: 'PASS' | 'FAIL' | 'IN_PROGRESS';
}

export interface SemesterResultBlock {
  semester_id: string;
  semester_name: string;
  semester_number: number;
  subjects: SubjectResultRow[];
  sgpa?: number | null;
  cgpa?: number | null;
  total_credits?: number | null;
  active_backlogs: number;
}

export interface StudentAcademicRecord {
  student_id: string;
  cgpa?: number | null;
  latest_sgpa?: number | null;
  total_active_backlogs: number;
  semesters: SemesterResultBlock[];
}

export const academicsService = {
  getStudentRecord: async (studentId: string): Promise<StudentAcademicRecord> => {
    const res = await api.get<StudentAcademicRecord>(`/academics/student/${studentId}/record`);
    return res.data;
  },

  recordBulkMarks: async (data: BulkMarksCreateData): Promise<MarkRecord[]> => {
    const res = await api.post<MarkRecord[]>('/marks', data);
    return res.data;
  },

  getStudentBacklogs: async (studentId: string): Promise<BacklogItem[]> => {
    const res = await api.get<BacklogItem[]>(`/academics/student/${studentId}/backlogs`);
    return res.data;
  },
};
