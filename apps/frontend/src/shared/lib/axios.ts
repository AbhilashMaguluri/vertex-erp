import axios, { AxiosError } from 'axios';
import { ApiErrorResponse } from '@scms/types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

let inMemoryToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  inMemoryToken = token;
};

export const getAccessToken = () => inMemoryToken;

api.interceptors.request.use((config) => {
  if (inMemoryToken) {
    config.headers.Authorization = `Bearer ${inMemoryToken}`;
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

function hardLogoutAndRedirect() {
  setAccessToken(null);
  try {
    localStorage.clear();
    sessionStorage.clear();
  } catch {
    // Storage may be unavailable (private browsing, etc.) — token is already cleared, safe to continue.
  }
  window.location.href = '/session-expired';
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config;
    const isAuthEndpoint =
      originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/refresh');

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !(originalRequest.headers as any)['_retry'] &&
      !isAuthEndpoint
    ) {
      (originalRequest.headers as any)['_retry'] = 'true';
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post<{ access_token: string }>(`${BASE_URL}/auth/refresh`, {}, { withCredentials: true })
            .then((res) => {
              setAccessToken(res.data.access_token);
              return res.data.access_token;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        hardLogoutAndRedirect();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
