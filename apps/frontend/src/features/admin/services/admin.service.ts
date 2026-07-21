import { api } from '@/shared/lib/axios';

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
  academic_year_id: string;
  number: number;
  name: string;
  start_date: string;
  end_date: string;
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
  getAcademicYears: async (): Promise<AcademicYear[]> => {
    const res = await api.get<AcademicYear[]>('/admin/academic-years');
    return res.data;
  },
  createAcademicYear: async (data: Partial<AcademicYear>): Promise<AcademicYear> => {
    const res = await api.post<AcademicYear>('/admin/academic-years', data);
    return res.data;
  },
  getSemesters: async (academicYearId?: string): Promise<Semester[]> => {
    const res = await api.get<Semester[]>('/admin/semesters', {
      params: { academic_year_id: academicYearId },
    });
    return res.data;
  },
  createSemester: async (data: Partial<Semester>): Promise<Semester> => {
    const res = await api.post<Semester>('/admin/semesters', data);
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
};
