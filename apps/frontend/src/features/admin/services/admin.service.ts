import { api } from '@/shared/lib/axios';
import { UserProfile } from '@/features/auth/services/auth.service';

export interface Department {
  id: string;
  code: string;
  name: string;
  description?: string;
  hod_user_id?: string;
  created_at: string;
}

export interface Section {
  id: string;
  department_id: string;
  name: string;
  /** Study year within the department's 4-year program (1=First .. 4=Fourth). */
  year: number | null;
  batch_year: number;
  created_at: string;
}

export interface AcademicYear {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  created_at: string;
}

export interface Semester {
  id: string;
  // Semesters are a fixed, institution-wide catalog (1-1 .. 4-2) — not
  // scoped to a particular academic year, so these are no longer guaranteed.
  academic_year_id?: string | null;
  number: number;
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  created_at: string;
}

export interface Subject {
  id: string;
  department_id: string;
  code: string;
  name: string;
  credits: number;
  max_mid_marks: number;
  max_internal_marks: number;
  max_external_marks: number;
  created_at: string;
}

export const adminService = {
  getDepartments: async (): Promise<Department[]> => {
    const res = await api.get<Department[]>('/admin/departments');
    return res.data;
  },
  createDepartment: async (data: Partial<Department>): Promise<Department> => {
    const res = await api.post<Department>('/admin/departments', data);
    return res.data;
  },
  updateDepartment: async (id: string, data: Partial<Department>): Promise<Department> => {
    const res = await api.patch<Department>(`/admin/departments/${id}`, data);
    return res.data;
  },
  getSections: async (departmentId?: string): Promise<Section[]> => {
    const res = await api.get<Section[]>('/admin/sections', {
      params: { department_id: departmentId },
    });
    return res.data;
  },
  createSection: async (data: Partial<Section>): Promise<Section> => {
    const res = await api.post<Section>('/admin/sections', data);
    return res.data;
  },
  updateSection: async (id: string, data: Partial<Section>): Promise<Section> => {
    const res = await api.patch<Section>(`/admin/sections/${id}`, data);
    return res.data;
  },
  deleteSection: async (id: string): Promise<void> => {
    await api.delete(`/admin/sections/${id}`);
  },
  getAcademicYears: async (): Promise<AcademicYear[]> => {
    const res = await api.get<AcademicYear[]>('/admin/academic-years');
    return res.data;
  },
  createAcademicYear: async (data: Partial<AcademicYear>): Promise<AcademicYear> => {
    const res = await api.post<AcademicYear>('/admin/academic-years', data);
    return res.data;
  },
  updateAcademicYear: async (id: string, data: Partial<AcademicYear>): Promise<AcademicYear> => {
    const res = await api.patch<AcademicYear>(`/admin/academic-years/${id}`, data);
    return res.data;
  },
  // Semesters are a fixed, institution-wide catalog (1-1 .. 4-2), seeded
  // once server-side — there is intentionally no create/update here.
  getSemesters: async (): Promise<Semester[]> => {
    const res = await api.get<Semester[]>('/admin/semesters');
    return res.data;
  },
  getSubjects: async (departmentId?: string): Promise<Subject[]> => {
    const res = await api.get<Subject[]>('/admin/subjects', {
      params: { department_id: departmentId },
    });
    return res.data;
  },
  createSubject: async (data: Partial<Subject>): Promise<Subject> => {
    const res = await api.post<Subject>('/admin/subjects', data);
    return res.data;
  },
  updateSubject: async (id: string, data: Partial<Subject>): Promise<Subject> => {
    const res = await api.patch<Subject>(`/admin/subjects/${id}`, data);
    return res.data;
  },
};

// --- User Management ------------------------------------------------------
export interface StudentProvisionDetails {
  roll_number: string;
  registration_number: string;
  date_of_birth: string;
  batch_year: number;
  section_id: string;
  semester_id: string;
}

export interface UserCreatePayload {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  department_id?: string;
  role: string;
  student_details?: StudentProvisionDetails;
  // Optional override for the auto-generated default password. STUDENT
  // accounts default to "<RollNumber>@vvit.net" server-side when omitted.
  password?: string;
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
  department_id?: string;
  role?: string;
}

export interface UserListItem {
  id: string;
  email: string;
  /** Roll number for students, `firstname.initial` for staff. Null on accounts
   *  created before Office Import. */
  username?: string | null;
  full_name: string;
  roles: string[];
  department_id?: string;
  is_active: boolean;
  force_password_change: boolean;
  last_login_at?: string;
  created_at: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedUsers {
  data: UserListItem[];
  pagination: PaginationMeta;
}

export interface AdminCreateUserResult {
  user: UserProfile;
  temporary_password: string;
  email_sent: boolean;
}

export interface AdminResetPasswordResult {
  temporary_password: string;
  email_sent: boolean;
}

export interface SessionInfo {
  id: string;
  created_at: string;
  expires_at: string;
  remember_me: boolean;
  user_agent?: string;
  ip_address?: string;
  is_current: boolean;
}

export interface UserListFilters {
  role?: string;
  department_id?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}

export const userAdminService = {
  listUsers: async (filters: UserListFilters): Promise<PaginatedUsers> => {
    const res = await api.get<PaginatedUsers>('/admin/users', { params: filters });
    return res.data;
  },
  getUser: async (userId: string): Promise<UserProfile> => {
    const res = await api.get<UserProfile>(`/admin/users/${userId}`);
    return res.data;
  },
  createUser: async (data: UserCreatePayload): Promise<AdminCreateUserResult> => {
    const res = await api.post<AdminCreateUserResult>('/admin/users', data);
    return res.data;
  },
  updateUser: async (userId: string, data: UserUpdatePayload): Promise<UserProfile> => {
    const res = await api.patch<UserProfile>(`/admin/users/${userId}`, data);
    return res.data;
  },
  deactivateUser: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/deactivate`);
  },
  activateUser: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/activate`);
  },
  resetPassword: async (userId: string): Promise<AdminResetPasswordResult> => {
    const res = await api.post<AdminResetPasswordResult>(`/admin/users/${userId}/reset-password`);
    return res.data;
  },
  listSessions: async (userId: string): Promise<SessionInfo[]> => {
    const res = await api.get<SessionInfo[]>(`/admin/users/${userId}/sessions`);
    return res.data;
  },
  forceLogout: async (userId: string): Promise<void> => {
    await api.post(`/admin/users/${userId}/force-logout`);
  },
  assignCounsellor: async (data: { student_id: string; counsellor_id: string; semester_id: string }): Promise<void> => {
    await api.post('/admin/users/assign-counsellor', data);
  },
  // Bulk provisioning lives in ./import.service.ts (Office Import).
};
