import type { AuthUser } from '@/api/auth';

export const TOKEN_KEY = 'insomnia-demo-token';
export const USER_KEY = 'insomnia-demo-user';
export const EXPIRES_KEY = 'insomnia-demo-expires-at';

export function loadStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function loadStoredExpiresAt() {
  const raw = localStorage.getItem(EXPIRES_KEY);
  if (!raw) {
    return 0;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

export function loadStoredUser(): AuthUser | null {
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

export function persistSession(token: string, user: AuthUser, expiresAt: number) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(EXPIRES_KEY, String(expiresAt));
}

export function clearStoredSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EXPIRES_KEY);
}
