import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45 seconds for complex legal RAG synthesis
});

// Request interceptor to attach Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle session expiration cleanly
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear invalid session tokens
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      
      // If not already on login or register, notify auth state
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.dispatchEvent(new CustomEvent('lexora:unauthorized'));
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(err: unknown, defaultMsg: string = 'An unexpected error occurred'): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
    }
    if (err.response?.data?.message) {
      return String(err.response.data.message);
    }
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return defaultMsg;
}

export default apiClient;
