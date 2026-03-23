import { defineStore } from 'pinia';

import type { Capability, UserRole } from '@/auth/access';
import { hasCapability } from '@/auth/access';
import { clearStoredSession, loadStoredExpiresAt, loadStoredToken, loadStoredUser, persistSession } from '@/auth/session';
import { fetchCurrentUser, loginRequest, type AuthUser, type LoginPayload } from '@/api/auth';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: loadStoredToken(),
    user: loadStoredUser() as AuthUser | null,
    expiresAt: loadStoredExpiresAt(),
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    role: (state): UserRole | null => state.user?.role || null,
    isExpired: (state) => Boolean(state.expiresAt && state.expiresAt <= Date.now()),
  },
  actions: {
    can(capability: Capability) {
      return hasCapability(this.user?.role, capability);
    },
    async ensureSession() {
      if (!this.token) {
        this.initialized = true;
        return false;
      }

      if (this.isExpired) {
        this.logout();
        this.initialized = true;
        return false;
      }

      if (this.user && this.initialized) {
        return true;
      }

      try {
        const { user } = await fetchCurrentUser();
        this.user = user;
        localStorage.setItem('insomnia-demo-user', JSON.stringify(user));
        this.initialized = true;
        return true;
      } catch {
        this.logout();
        this.initialized = true;
        return false;
      }
    },
    async login(payload: LoginPayload) {
      const data = await loginRequest(payload);
      this.token = data.access_token;
      this.user = data.user;
      this.expiresAt = Date.now() + data.expires_in * 1000;
      this.initialized = true;
      persistSession(data.access_token, data.user, this.expiresAt);
      return data;
    },
    logout() {
      this.token = '';
      this.user = null;
      this.expiresAt = 0;
      this.initialized = true;
      clearStoredSession();
    },
  },
});
