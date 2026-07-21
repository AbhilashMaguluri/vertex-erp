import { api } from '@/shared/lib/axios';

export interface ParentCommunication {
  id: string;
  student_id: string;
  counsellor_id: string;
  communication_date: string;
  communication_time?: string;
  mode: string;
  parent_name: string;
  relation: string;
  contact_number: string;
  summary: string;
  concerns?: string;
  action_items?: string;
  outcome: string;
  follow_up_date?: string;
  created_at: string;
}

export interface ParentCommunicationCreateData {
  student_id: string;
  communication_date: string;
  communication_time?: string;
  mode: string;
  parent_name: string;
  relation: string;
  contact_number: string;
  summary: string;
  concerns?: string;
  action_items?: string;
  outcome: string;
  follow_up_date?: string;
}

export const parentService = {
  logCommunication: async (data: ParentCommunicationCreateData): Promise<ParentCommunication> => {
    const res = await api.post<ParentCommunication>('/parent-communication', data);
    return res.data;
  },

  getStudentCommunications: async (studentId: string): Promise<ParentCommunication[]> => {
    const res = await api.get<ParentCommunication[]>(`/parent-communication/student/${studentId}`);
    return res.data;
  },
};
