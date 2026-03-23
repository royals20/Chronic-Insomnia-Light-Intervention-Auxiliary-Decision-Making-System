import apiClient from '@/api/client';
import type { UserRole } from '@/auth/access';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthUser {
  id: number;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  message: string;
  user: AuthUser;
}

export interface AuthMeResponse {
  user: AuthUser;
  checked_at: string;
}

export async function loginRequest(payload: LoginPayload) {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', payload);
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await apiClient.get<AuthMeResponse>('/auth/me');
  return data;
}
