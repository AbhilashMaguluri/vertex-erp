import { api, setAccessToken } from '@/shared/lib/axios';
import {
  LoginFormData,
  ForgotPasswordFormData,
  ResetPasswordFormData,
  ChangePasswordFormData,
} from '../schemas/auth.schema';

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
  department_id?: string;
  force_password_change: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  force_password_change: boolean;
  department_id?: string;
  roles: string[];
  permissions: string[];
  last_login_at?: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: UserSummary;
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

export const authService = {
  login: async (credentials: LoginFormData): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
    setAccessToken(response.data.access_token);
    return response.data;
  },

  refresh: async (): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh');
    setAccessToken(response.data.access_token);
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } finally {
      setAccessToken(null);
    }
  },

  getCurrentUser: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/auth/me');
    return response.data;
  },

  changePassword: async (data: ChangePasswordFormData): Promise<void> => {
    await api.post('/auth/change-password', {
      current_password: data.currentPassword,
      new_password: data.newPassword,
    });
  },

  forgotPassword: async (data: ForgotPasswordFormData): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/forgot-password', data);
    return response.data;
  },

  resetPassword: async (token: string, data: ResetPasswordFormData): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/reset-password', {
      token,
      new_password: data.password,
    });
    return response.data;
  },

  getSessions: async (): Promise<SessionInfo[]> => {
    const response = await api.get<SessionInfo[]>('/auth/sessions');
    return response.data;
  },

  revokeSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/auth/sessions/${sessionId}`);
  },
};
