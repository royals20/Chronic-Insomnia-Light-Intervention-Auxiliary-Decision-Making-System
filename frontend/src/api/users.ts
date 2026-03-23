import apiClient from '@/api/client';
import type { UserRole } from '@/auth/access';

export interface UserRecord {
  id: number;
  username: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserCreatePayload {
  username: string;
  full_name: string;
  role: UserRole;
  password: string;
  is_active: boolean;
}

export interface UserUpdatePayload {
  username?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export async function fetchUsers() {
  const { data } = await apiClient.get<UserRecord[]>('/users');
  return data;
}

export async function createUser(payload: UserCreatePayload) {
  const { data } = await apiClient.post<UserRecord>('/users', payload);
  return data;
}

export async function updateUser(userId: number, payload: UserUpdatePayload) {
  const { data } = await apiClient.put<UserRecord>(`/users/${userId}`, payload);
  return data;
}

export async function resetUserPassword(userId: number, newPassword: string) {
  const { data } = await apiClient.post<UserRecord>(`/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
  return data;
}

export async function toggleUserActive(userId: number) {
  const { data } = await apiClient.post<UserRecord>(`/users/${userId}/toggle-active`);
  return data;
}
