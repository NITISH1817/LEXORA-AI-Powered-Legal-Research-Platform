import { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from 'react';
import apiClient from '../api/client';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('token') || localStorage.getItem('access_token');
  });
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    delete apiClient.defaults.headers.common['Authorization'];
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const res = await apiClient.get<User>('/api/auth/me');
      setUser(res.data);
    } catch (err) {
      console.warn('Authentication token verification failed:', err);
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('token', token);
      localStorage.setItem('access_token', token);
      fetchUser();
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      setUser(null);
      setIsLoading(false);
    }
  }, [token, fetchUser]);

  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('lexora:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('lexora:unauthorized', handleUnauthorized);
    };
  }, [logout]);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', pass);

    try {
      const res = await apiClient.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const newToken = res.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      localStorage.setItem('access_token', newToken);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

      // Fetch user profile immediately
      const userRes = await apiClient.get<User>('/api/auth/me');
      setUser(userRes.data);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    if (token) {
      await fetchUser();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        logout,
        isAuthenticated: !!token,
        isLoading,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
