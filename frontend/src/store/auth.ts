import { create } from 'zustand';
import type { User } from '../types';

const DEV_USER: User = {
  id: 1,
  username: 'admin',
  full_name: 'Administrador',
  email: 'admin@autofact.local',
  role: 'admin',
  is_active: true,
  created_at: '',
  updated_at: '',
};

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User, refreshToken?: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: DEV_USER,
  token: 'dev-token',
  refreshToken: 'dev-refresh-token',
  isAuthenticated: true,
  login: (token: string, user: User, refreshToken?: string) => {
    set({ token, user, isAuthenticated: true, refreshToken: refreshToken ?? null });
  },
  logout: () => {
    set({ user: DEV_USER, token: 'dev-token', refreshToken: 'dev-refresh-token', isAuthenticated: true });
  },
  setUser: (user: User) => {
    set({ user });
  },
  setToken: (token: string) => {
    set({ token });
  },
}));
