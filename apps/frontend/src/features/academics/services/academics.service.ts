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
  attempts_count: number;
  status: string;
  created_at: string;
}

export const academicsService = {
  recordBulkMarks: async (data: BulkMarksCreateData): Promise<MarkRecord[]> => {
    const res = await api.post<MarkRecord[]>('/marks', data);
    return res.data;
  },

  getStudentBacklogs: async (studentId: string): Promise<BacklogItem[]> => {
    const res = await api.get<BacklogItem[]>(`/academics/student/${studentId}/backlogs`);
    return res.data;
  },
};
