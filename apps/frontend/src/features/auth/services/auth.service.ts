import { api, setAccessToken } from '@/shared/lib/axios';
import { LoginFormData, ForgotPasswordFormData, ResetPasswordFormData } from '../schemas/auth.schema';

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  department_id?: string;
  roles: string[];
  permissions: string[];
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
}

export const authService = {
  login: async (credentials: LoginFormData): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
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
};
