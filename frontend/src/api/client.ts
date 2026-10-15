import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { Analysis, AnalysisCreate, AnalysisListResponse, AnalysisUpdate, AuthConfig, User } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setAccessToken(null);
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/callback')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  getConfig: () => api.get<AuthConfig>('/auth/config'),
  loginStart: () => api.get<{ authorization_url: string; state: string; nonce: string; code_verifier: string }>('/auth/login'),
  logout: () => api.post<{ logout_url: string }>('/auth/logout'),
  getMe: () => api.get<User>('/auth/me'),
};

export const analysesApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; analysis_type?: string }) =>
    api.get<AnalysisListResponse>('/analyses', { params }),
  get: (id: number) => api.get<Analysis>(`/analyses/${id}`),
  create: (data: AnalysisCreate) => api.post<Analysis>('/analyses', data),
  update: (id: number, data: AnalysisUpdate) => api.patch<Analysis>(`/analyses/${id}`, data),
  delete: (id: number) => api.delete(`/analyses/${id}`),
};

export default api;