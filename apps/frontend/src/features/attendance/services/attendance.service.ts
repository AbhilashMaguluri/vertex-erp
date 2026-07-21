import { api } from '@/shared/lib/axios';

export interface StudentAttendanceItem {
  student_id: string;
  status: string; // PRESENT, ABSENT, ON_DUTY, MEDICAL_LEAVE
}

export interface BulkAttendanceCreateData {
  subject_id: string;
  date: string;
  records: StudentAttendanceItem[];
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  subject_id: string;
  date: string;
  status: string;
  recorded_by: string;
  created_at: string;
}

export interface SubjectAttendanceSummary {
  subject_id: string;
  subject_code: string;
  subject_name: string;
  total_classes: number;
  attended_classes: number;
  percentage: number;
}

export interface StudentAttendanceSummary {
  student_id: string;
  overall_percentage: number;
  subject_summaries: SubjectAttendanceSummary[];
}

export const attendanceService = {
  recordBulkAttendance: async (data: BulkAttendanceCreateData): Promise<AttendanceRecord[]> => {
    const res = await api.post<AttendanceRecord[]>('/attendance', data);
    return res.data;
  },

  getStudentAttendanceSummary: async (studentId: string): Promise<StudentAttendanceSummary> => {
    const res = await api.get<StudentAttendanceSummary>(`/attendance/student/${studentId}`);
    return res.data;
  },

  requestCorrection: async (attendanceRecordId: string, newStatus: string, reason: string): Promise<any> => {
    const res = await api.post('/attendance/corrections', {
      attendance_record_id: attendanceRecordId,
      new_status: newStatus,
      reason,
    });
    return res.data;
  },
};
