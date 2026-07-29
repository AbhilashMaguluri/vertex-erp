import { api } from '@/shared/lib/axios';

export interface ActionItem {
  id?: string;
  description: string;
  due_date: string;
  status?: string;
  assigned_to_user_id?: string;
}

export interface CounsellingSession {
  id: string;
  student_id: string;
  counsellor_id: string;
  session_date: string;
  session_type: string;
  mode: string;
  observations: string;
  recommendations?: string | null;
  student_commitments?: string | null;
  /** Always null when the viewer is a student — the API strips it server-side.
   *  Never render this field in a student-facing view. */
  confidential_notes?: string | null;
  follow_up_required: boolean;
  follow_up_date?: string;
  student_acknowledged: boolean;
  acknowledged_at?: string;
  risk_assessment?: string;
  confidential: boolean;
  action_items: ActionItem[];
  created_at: string;
}

export interface SessionCreateData {
  student_id: string;
  session_date: string;
  session_type: string;
  mode: string;
  observations: string;
  recommendations?: string;
  student_commitments?: string;
  confidential_notes?: string;
  follow_up_required?: boolean;
  follow_up_date?: string;
  risk_assessment?: string;
  confidential?: boolean;
  action_items?: ActionItem[];
}

export interface ChartBucket {
  bucket: string;
  count: number;
}

export interface UpcomingFollowUp {
  id: string;
  description: string;
  due_date: string;
  is_overdue: boolean;
  is_due_today: boolean;
  student_id: string;
  student_name: string;
  student_roll_number: string;
  session_id: string;
  session_date?: string | null;
}

/** Machine-readable triggers behind an attention row's prose `reason`, so the
 *  UI can render a severity dot per trigger instead of parsing the sentence. */
export type AttentionFlag =
  | 'HIGH_RISK'
  | 'LOW_ATTENDANCE'
  | 'MANY_BACKLOGS'
  | 'BACKLOGS'
  | 'NEVER_COUNSELLED';

export interface AttentionStudent {
  id: string;
  roll_number: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  section_name?: string | null;
  study_year?: number | null;
  risk_level: string;
  attendance_percentage?: number | null;
  cgpa?: number | null;
  active_backlogs: number;
  last_session_date?: string | null;
  reason: string;
  flags: AttentionFlag[];
}

export interface ActivityEntry {
  session_id: string;
  student_id: string;
  student_name: string;
  student_roll_number: string;
  session_type: string;
  mode: string;
  session_date: string;
  recorded_at: string;
  follow_up_required: boolean;
}

/** One item on today's agenda.
 *
 *  There is no clock time here on purpose: the schema stores `session_date`
 *  and `due_date` as plain dates, so nothing in this system knows what time a
 *  meeting happens. Agenda items are ordered by urgency, not by hour. */
export interface AgendaEntry {
  kind: 'FOLLOW_UP' | 'SESSION';
  reference_id: string;
  student_id: string;
  student_name: string;
  student_roll_number: string;
  label: string;
  due_date: string;
  is_overdue: boolean;
}

export interface CounsellorDashboard {
  total_students: number;
  male: number;
  female: number;
  gender_unknown: number;
  average_attendance?: number | null;
  average_cgpa?: number | null;
  sessions_total: number;
  sessions_today: number;
  sessions_this_month: number;
  sessions_acknowledged: number;
  follow_ups_pending: number;
  follow_ups_completed: number;
  follow_ups_overdue: number;
  follow_ups_upcoming: number;
  active_cases: number;
  high_risk_count: number;
  below_attendance_count: number;
  with_backlogs_count: number;
  risk_high: number;
  risk_medium: number;
  risk_low: number;
  by_year: ChartBucket[];
  by_section: ChartBucket[];
  by_risk: ChartBucket[];
  by_attendance_band: ChartBucket[];
  sessions_by_month: ChartBucket[];
  sessions_by_type: ChartBucket[];
  upcoming_follow_ups: UpcomingFollowUp[];
  students_needing_attention: AttentionStudent[];
  recent_activity: ActivityEntry[];
  agenda_today: AgendaEntry[];
}

export const counsellingService = {
  createSession: async (data: SessionCreateData): Promise<CounsellingSession> => {
    const res = await api.post<CounsellingSession>('/counselling/sessions', data);
    return res.data;
  },

  getSessions: async (studentId?: string, counsellorId?: string): Promise<CounsellingSession[]> => {
    const res = await api.get<CounsellingSession[]>('/counselling/sessions', {
      params: { student_id: studentId, counsellor_id: counsellorId },
    });
    return res.data;
  },

  getSessionById: async (sessionId: string): Promise<CounsellingSession> => {
    const res = await api.get<CounsellingSession>(`/counselling/sessions/${sessionId}`);
    return res.data;
  },

  getDashboard: async (): Promise<CounsellorDashboard> => {
    const res = await api.get<CounsellorDashboard>('/counselling/dashboard');
    return res.data;
  },

  /** A student's own counselling history. The backend resolves the student
   *  from the session token and strips confidential notes. */
  getMySessions: async (): Promise<CounsellingSession[]> => {
    const res = await api.get<CounsellingSession[]>('/counselling/my-sessions');
    return res.data;
  },

  getFollowUps: async (status?: string): Promise<ActionItem[]> => {
    const res = await api.get<ActionItem[]>('/counselling/follow-ups', {
      params: { status },
    });
    return res.data;
  },

  updateFollowUpStatus: async (actionItemId: string, status: string): Promise<ActionItem> => {
    const res = await api.patch<ActionItem>(`/counselling/follow-ups/${actionItemId}/status`, {
      status,
    });
    return res.data;
  },

  /** Complete and/or reschedule a follow-up. The API rejects a due date in the
   *  past and reopens a completed item that gets rescheduled. */
  updateFollowUp: async (
    actionItemId: string,
    changes: { status?: string; due_date?: string }
  ): Promise<ActionItem> => {
    const res = await api.patch<ActionItem>(`/counselling/follow-ups/${actionItemId}`, changes);
    return res.data;
  },

  acknowledgeSession: async (sessionId: string): Promise<CounsellingSession> => {
    const res = await api.post<CounsellingSession>(`/counselling/sessions/${sessionId}/acknowledge`);
    return res.data;
  },
};
