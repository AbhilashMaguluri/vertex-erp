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

export const studentService = {
  getStudent360: async (studentId: string): Promise<Student360Data> => {
    const res = await api.get<Student360Data>(`/students/${studentId}/workspace`);
    return res.data;
  },

  updateRiskFlag: async (studentId: string, risk_level: string, reason: string): Promise<StudentProfile> => {
    const res = await api.patch<StudentProfile>(`/students/${studentId}/risk`, {
      risk_level,
      reason,
    });
    return res.data;
  },
};
