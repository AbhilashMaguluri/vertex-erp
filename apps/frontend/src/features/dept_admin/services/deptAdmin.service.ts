import { api } from '@/shared/lib/axios';

/**
 * Department Administrator API Service.
 */

export interface DeptAdminUser {
  id: string;
  email: string;
  username?: string | null;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string | null;
  department_id?: string | null;
  department_code?: string | null;
  department_name?: string | null;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface CreateDeptAdminData {
  email: string;
  first_name: string;
  last_name: string;
  department_id: string;
  phone?: string;
  username?: string;
}

export interface UpdateDeptAdminData {
  first_name?: string;
  last_name?: string;
  department_id?: string;
  phone?: string;
  is_active?: boolean;
}

export interface DeptDashboardMetrics {
  department_id: string;
  department_code: string;
  department_name: string;
  total_students: number;
  faculty_count: number;
  counselor_count: number;
  attendance_percentage: number;
  pending_counseling_sessions: number;
  subject_count: number;
  section_count: number;
  recent_activity_count: number;
}

export const deptAdminService = {
  // Super Admin Management
  listDeptAdmins: async (): Promise<DeptAdminUser[]> => {
    const res = await api.get<DeptAdminUser[]>('/admin/dept-admins');
    return res.data;
  },

  createDeptAdmin: async (data: CreateDeptAdminData): Promise<DeptAdminUser> => {
    const res = await api.post<DeptAdminUser>('/admin/dept-admins', data);
    return res.data;
  },

  updateDeptAdmin: async (
    userId: string,
    data: UpdateDeptAdminData,
  ): Promise<DeptAdminUser> => {
    const res = await api.put<DeptAdminUser>(`/admin/dept-admins/${userId}`, data);
    return res.data;
  },

  resetPassword: async (userId: string): Promise<{ message: string; temporary_password: string }> => {
    const res = await api.post<{ message: string; temporary_password: string }>(
      `/admin/dept-admins/${userId}/reset-password`,
    );
    return res.data;
  },

  // Department Admin Dashboard
  getDashboardMetrics: async (): Promise<DeptDashboardMetrics> => {
    const res = await api.get<DeptDashboardMetrics>('/dept-admin/dashboard');
    return res.data;
  },
};
