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
  follow_up_required?: boolean;
  follow_up_date?: string;
  risk_assessment?: string;
  confidential?: boolean;
  action_items?: ActionItem[];
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

  acknowledgeSession: async (sessionId: string): Promise<CounsellingSession> => {
    const res = await api.post<CounsellingSession>(`/counselling/sessions/${sessionId}/acknowledge`);
    return res.data;
  },
};
