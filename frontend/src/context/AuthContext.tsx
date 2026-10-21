import React, { useState, useEffect, useCallback, type ReactNode } from 'react';
import apiClient from '../api/client';
import { AuthContext, type User } from './auth-types';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('token') || localStorage.getItem('access_token');
  });
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    const initialToken = localStorage.getItem('token') || localStorage.getItem('access_token');
    return !!initialToken;
  });

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    delete apiClient.defaults.headers.common['Authorization'];
    setIsLoading(false);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const res = await apiClient.get<User>('/api/auth/me');
      setUser(res.data);
    } catch (err) {
      console.warn('Authentication token refresh failed:', err);
      logout();
    }
  }, [token, logout]);

  // Synchronize token and fetch user asynchronously without synchronous setState
  useEffect(() => {
    let isCancelled = false;

    if (!token) {
      delete apiClient.defaults.headers.common['Authorization'];
      return;
    }

    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('token', token);
    localStorage.setItem('access_token', token);

    apiClient
      .get<User>('/api/auth/me')
      .then((res) => {
        if (!isCancelled) {
          setUser(res.data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          console.warn('Authentication token verification failed:', err);
          logout();
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [token, logout]);

  // Listen for global unauthorized events emitted by apiClient response interceptor
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

export default AuthProvider;
