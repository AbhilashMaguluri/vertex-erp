import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/axios';
import {
  CounsellorContactProfile,
  AssignedStudentContact,
  AppointmentRequest,
  CommunicationTimelineLog,
  AIMeetingBriefing,
  CommunicationTemplate,
  InstitutionalChannelPolicy,
  CampusEmergencyContact,
  StudentPrivacySettings,
  ReachOutAuditLog,
} from '../types/reachOut';

export const reachOutKeys = {
  all: ['reach-out'] as const,
  myCounsellor: () => [...reachOutKeys.all, 'my-counsellor'] as const,
  counsellors: (deptId?: string) => [...reachOutKeys.all, 'counsellors', deptId || 'all'] as const,
  caseload: (counsellorId?: string) => [...reachOutKeys.all, 'caseload', counsellorId || 'self'] as const,
  aiBriefing: (studentId: string) => [...reachOutKeys.all, 'ai-briefing', studentId] as const,
  timeline: (studentId: string) => [...reachOutKeys.all, 'timeline', studentId] as const,
  appointments: () => [...reachOutKeys.all, 'appointments'] as const,
  privacy: () => [...reachOutKeys.all, 'privacy'] as const,
  templates: () => [...reachOutKeys.all, 'templates'] as const,
  emergencyContacts: () => [...reachOutKeys.all, 'emergency-contacts'] as const,
  channelPolicy: () => [...reachOutKeys.all, 'channel-policy'] as const,
  adminCounsellors: () => [...reachOutKeys.all, 'admin-counsellors'] as const,
  auditLogs: () => [...reachOutKeys.all, 'audit-logs'] as const,
};

export function useMyCounsellor() {
  return useQuery<{ assigned: boolean; profile?: CounsellorContactProfile; message?: string }>({
    queryKey: reachOutKeys.myCounsellor(),
    queryFn: async () => {
      const res = await api.get('/reach-out/my-counsellor');
      return res.data;
    },
  });
}

export function useCounsellors(departmentId?: string) {
  return useQuery<CounsellorContactProfile[]>({
    queryKey: reachOutKeys.counsellors(departmentId),
    queryFn: async () => {
      const res = await api.get('/reach-out/counsellors', {
        params: departmentId ? { department_id: departmentId } : {},
      });
      return res.data;
    },
  });
}

export function useAssignedStudentsCaseload(counsellorId?: string) {
  return useQuery<AssignedStudentContact[]>({
    queryKey: reachOutKeys.caseload(counsellorId),
    queryFn: async () => {
      const res = await api.get('/reach-out/caseload', {
        params: counsellorId ? { counsellor_id: counsellorId } : {},
      });
      return res.data;
    },
  });
}

export function useAIMeetingBriefing(studentId: string, enabled: boolean = false) {
  return useQuery<AIMeetingBriefing>({
    queryKey: reachOutKeys.aiBriefing(studentId),
    queryFn: async () => {
      const res = await api.get(`/reach-out/caseload/${studentId}/ai-briefing`);
      return res.data;
    },
    enabled: enabled && Boolean(studentId),
  });
}

export function useStudentTimeline(studentId: string, enabled: boolean = false) {
  return useQuery<CommunicationTimelineLog[]>({
    queryKey: reachOutKeys.timeline(studentId),
    queryFn: async () => {
      const res = await api.get(`/reach-out/caseload/${studentId}/timeline`);
      return res.data;
    },
    enabled: enabled && Boolean(studentId),
  });
}

export function useAppointments() {
  return useQuery<AppointmentRequest[]>({
    queryKey: reachOutKeys.appointments(),
    queryFn: async () => {
      const res = await api.get('/reach-out/appointments');
      return res.data;
    },
  });
}

export function useMyPrivacySettings() {
  return useQuery<StudentPrivacySettings>({
    queryKey: reachOutKeys.privacy(),
    queryFn: async () => {
      const res = await api.get('/reach-out/privacy');
      return res.data;
    },
  });
}

export function useCommunicationTemplates() {
  return useQuery<CommunicationTemplate[]>({
    queryKey: reachOutKeys.templates(),
    queryFn: async () => {
      const res = await api.get('/reach-out/templates');
      return res.data;
    },
  });
}

export function useCampusEmergencyContacts() {
  return useQuery<CampusEmergencyContact[]>({
    queryKey: reachOutKeys.emergencyContacts(),
    queryFn: async () => {
      const res = await api.get('/reach-out/emergency-contacts');
      return res.data;
    },
  });
}

export function useInstitutionalChannelPolicy() {
  return useQuery<InstitutionalChannelPolicy>({
    queryKey: reachOutKeys.channelPolicy(),
    queryFn: async () => {
      const res = await api.get('/reach-out/channel-policy');
      return res.data;
    },
  });
}

export function useAdminCounsellors() {
  return useQuery<CounsellorContactProfile[]>({
    queryKey: reachOutKeys.adminCounsellors(),
    queryFn: async () => {
      const res = await api.get('/reach-out/counsellors');
      return res.data;
    },
  });
}

export function useAdminAuditLogs() {
  return useQuery<ReachOutAuditLog[]>({
    queryKey: reachOutKeys.auditLogs(),
    queryFn: async () => {
      const res = await api.get('/reach-out/admin/audit-logs');
      return res.data;
    },
  });
}

// Mutations
export function useToggleFavoriteStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ studentId, isFavorite }: { studentId: string; isFavorite: boolean }) => {
      if (isFavorite) {
        await api.delete(`/reach-out/favorites/${studentId}`);
      } else {
        await api.post(`/reach-out/favorites/${studentId}`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.all });
    },
  });
}

export function useCreateAppointment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { request_type: string; preferred_date: string; preferred_time_slot: string; reason?: string }) => {
      const res = await api.post('/reach-out/appointments', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.appointments() });
    },
  });
}

export function useUpdateAppointmentStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ appointmentId, status, rescheduled_date, rescheduled_slot, counsellor_notes }: { appointmentId: string; status: string; rescheduled_date?: string; rescheduled_slot?: string; counsellor_notes?: string }) => {
      const res = await api.put(`/reach-out/appointments/${appointmentId}/status`, { status, rescheduled_date, rescheduled_slot, counsellor_notes });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.appointments() });
    },
  });
}

export function useLogCommunication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ studentId, data }: { studentId: string; data: { channel: string; direction: string; summary: string; sentiment: string; action_outcome: string; duration_minutes?: number; follow_up_required: boolean; follow_up_date?: string } }) => {
      const res = await api.post(`/reach-out/caseload/${studentId}/timeline`, data);
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.timeline(variables.studentId) });
      queryClient.invalidateQueries({ queryKey: reachOutKeys.caseload() });
    },
  });
}

export function useUpdatePrivacySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StudentPrivacySettings) => {
      const res = await api.put('/reach-out/privacy', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.privacy() });
      queryClient.invalidateQueries({ queryKey: reachOutKeys.myCounsellor() });
    },
  });
}

export function useUpdateAdminCounsellor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ counsellorId, data }: { counsellorId: string; data: Partial<CounsellorContactProfile> }) => {
      const res = await api.put(`/reach-out/admin/counsellors/${counsellorId}`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.all });
    },
  });
}

export function useAdminCreateEmergencyContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; category: string; phone: string; email?: string; location?: string; is_24_7: boolean; display_order: number }) => {
      const res = await api.post('/reach-out/admin/emergency-contacts', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.emergencyContacts() });
      queryClient.invalidateQueries({ queryKey: reachOutKeys.auditLogs() });
    },
  });
}

export function useAdminDeleteEmergencyContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contactId: string) => {
      await api.delete(`/reach-out/admin/emergency-contacts/${contactId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.emergencyContacts() });
      queryClient.invalidateQueries({ queryKey: reachOutKeys.auditLogs() });
    },
  });
}

export function useUpdateChannelPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => {
      const res = await api.put('/reach-out/admin/channel-policy', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reachOutKeys.channelPolicy() });
      queryClient.invalidateQueries({ queryKey: reachOutKeys.auditLogs() });
    },
  });
}
