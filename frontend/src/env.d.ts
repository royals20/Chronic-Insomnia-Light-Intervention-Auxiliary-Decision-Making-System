/// <reference types="vite/client" />

import 'vue-router';

import type { UserRole } from '@/auth/access';

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module 'vue-router' {
  interface RouteMeta {
    title?: string;
    description?: string;
    guestOnly?: boolean;
    requiresAuth?: boolean;
    allowedRoles?: UserRole[];
    sectionKey?: string;
  }
}
