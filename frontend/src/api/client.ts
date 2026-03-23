import axios from 'axios';
import { ElMessage } from 'element-plus';

import { clearStoredSession, loadStoredToken } from '@/auth/session';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = loadStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    if (status === 401) {
      clearStoredSession();
      const currentPath = `${window.location.pathname}${window.location.search}`;
      if (!window.location.pathname.startsWith('/login')) {
        const redirect = encodeURIComponent(currentPath || '/dashboard');
        window.location.assign(`/login?redirect=${redirect}`);
      }
    }

    if (status === 403) {
      ElMessage.error(error.response?.data?.detail || '当前角色无权限');
    }

    return Promise.reject(error);
  },
);

export default apiClient;
