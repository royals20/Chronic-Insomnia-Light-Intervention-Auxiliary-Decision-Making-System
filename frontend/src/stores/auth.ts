import { defineStore } from 'pinia';

import apiClient from '@/api/client';

interface LoginPayload {
  username: string;
  password: string;
}

interface AuthUser {
  id: number;
  username: string;
  full_name: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  message: string;
  user: AuthUser;
}

const TOKEN_KEY = 'insomnia-demo-token';
const USER_KEY = 'insomnia-demo-user';

function loadUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: loadUser() as AuthUser | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async login(payload: LoginPayload) {
      const { data } = await apiClient.post<LoginResponse>('/auth/login', payload);
      this.token = data.access_token;
      this.user = data.user;
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      return data;
    },
    logout() {
      this.token = '';
      this.user = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    },
  },
});
