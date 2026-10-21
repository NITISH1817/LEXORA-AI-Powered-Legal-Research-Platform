import { createContext } from 'react';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
}

export interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
