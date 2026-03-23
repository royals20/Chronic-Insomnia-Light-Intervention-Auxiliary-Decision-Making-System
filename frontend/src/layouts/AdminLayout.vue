<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand-panel">
        <span class="brand-panel__badge">Research Cockpit</span>
        <h1>慢性失眠光干预科研驾驶舱</h1>
        <p>围绕数据治理、规则评估、因果训练与结果解释组织统一科研流程。</p>
      </div>

      <div class="sidebar-summary">
        <DataBadge :label="roleLabel(authStore.role)" tone="primary" />
        <DataBadge label="科研辅助系统" tone="warning" />
      </div>

      <div class="menu-groups">
        <section v-for="group in menuGroups" :key="group.key" class="menu-group">
          <span class="menu-group__title">{{ group.title }}</span>
          <nav class="menu-list">
            <button
              v-for="item in group.items"
              :key="item.path"
              type="button"
              class="menu-item"
              :class="{ 'is-active': activeMenu === item.path }"
              @click="goTo(item.path)"
            >
              <span class="menu-item__label">{{ item.label }}</span>
              <small>{{ item.description }}</small>
            </button>
          </nav>
        </section>
      </div>
    </aside>

    <div class="app-main-shell">
      <header class="app-topbar">
        <div class="app-topbar__left">
          <el-button class="nav-trigger" plain @click="drawerVisible = true">导航</el-button>
          <div>
            <div class="app-topbar__eyebrow">科研平台 / {{ roleLabel(authStore.role) }}</div>
            <h2>{{ pageTitle }}</h2>
            <p>{{ pageDescription }}</p>
          </div>
        </div>

        <div class="app-topbar__right">
          <div class="user-block">
            <strong>{{ authStore.user?.full_name || '未登录用户' }}</strong>
            <span>{{ authStore.user?.username || '--' }}</span>
          </div>
          <el-button type="primary" plain @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <main class="app-content">
        <RouterView />
      </main>
    </div>

    <el-drawer v-model="drawerVisible" direction="ltr" size="320px" :with-header="false" class="nav-drawer">
      <div class="drawer-inner">
        <div class="brand-panel brand-panel--drawer">
          <span class="brand-panel__badge">Research Cockpit</span>
          <h1>慢性失眠光干预科研驾驶舱</h1>
          <p>按角色裁剪入口，支持答辩展示与科研流程演示。</p>
        </div>

        <div class="sidebar-summary sidebar-summary--drawer">
          <DataBadge :label="roleLabel(authStore.role)" tone="primary" />
          <DataBadge label="科研辅助系统" tone="warning" />
        </div>

        <div class="menu-groups">
          <section v-for="group in menuGroups" :key="`drawer-${group.key}`" class="menu-group">
            <span class="menu-group__title">{{ group.title }}</span>
            <nav class="menu-list">
              <button
                v-for="item in group.items"
                :key="`drawer-${item.path}`"
                type="button"
                class="menu-item"
                :class="{ 'is-active': activeMenu === item.path }"
                @click="goToFromDrawer(item.path)"
              >
                <span class="menu-item__label">{{ item.label }}</span>
                <small>{{ item.description }}</small>
              </button>
            </nav>
          </section>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import DataBadge from '@/components/DataBadge.vue';
import { appMenu, hasAnyRole, roleLabel } from '@/auth/access';
import { useAuthStore } from '@/stores/auth';

interface MenuGroup {
  key: string;
  title: string;
  items: typeof appMenu;
}

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const drawerVisible = ref(false);

const visibleMenuItems = computed(() =>
  appMenu.filter((item) => hasAnyRole(authStore.role, item.roles)),
);

const pageTitle = computed(() => (route.meta.title as string | undefined) || '科研平台');
const pageDescription = computed(
  () => (route.meta.description as string | undefined) || '按角色加载可访问的页面与操作。',
);

const activeMenu = computed(() => {
  const matched = visibleMenuItems.value.find((item) =>
    item.path === '/dashboard' ? route.path === item.path : route.path.startsWith(item.path),
  );
  return matched?.path || '/dashboard';
});

const menuGroups = computed<MenuGroup[]>(() => {
  const grouped = {
    overview: [] as typeof appMenu,
    data: [] as typeof appMenu,
    analysis: [] as typeof appMenu,
    admin: [] as typeof appMenu,
  };

  for (const item of visibleMenuItems.value) {
    if (item.path === '/dashboard') {
      grouped.overview.push(item);
      continue;
    }
    if (['/subjects', '/data-center', '/data-quality'].includes(item.path)) {
      grouped.data.push(item);
      continue;
    }
    if (['/recommendation-center', '/report-center', '/model-center', '/causal-results'].includes(item.path)) {
      grouped.analysis.push(item);
      continue;
    }
    grouped.admin.push(item);
  }

  return [
    { key: 'overview', title: '总览入口', items: grouped.overview },
    { key: 'data', title: '数据治理', items: grouped.data },
    { key: 'analysis', title: '分析决策', items: grouped.analysis },
    { key: 'admin', title: '系统管理', items: grouped.admin },
  ].filter((group) => group.items.length > 0);
});

function goTo(path: string) {
  void router.push(path);
}

function goToFromDrawer(path: string) {
  drawerVisible.value = false;
  void router.push(path);
}

function handleLogout() {
  authStore.logout();
  void router.push('/login');
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 308px minmax(0, 1fr);
}

.app-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 22px 18px;
  overflow-y: auto;
  background:
    radial-gradient(circle at top, rgba(87, 170, 189, 0.18), transparent 26%),
    linear-gradient(180deg, #102f46 0%, #0e2334 100%);
  color: #fff;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-panel {
  padding: 20px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.brand-panel__badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.brand-panel h1 {
  margin: 16px 0 10px;
  font-size: 30px;
  line-height: 1.02;
}

.brand-panel p {
  margin: 0;
  color: rgba(255, 255, 255, 0.74);
  line-height: 1.7;
}

.sidebar-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.menu-groups {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.menu-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-group__title {
  padding: 0 6px;
  color: rgba(255, 255, 255, 0.54);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  position: relative;
  width: 100%;
  padding: 16px 16px 15px 18px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    background-color var(--transition-base),
    border-color var(--transition-base),
    transform var(--transition-fast);
}

.menu-item::before {
  content: '';
  position: absolute;
  top: 16px;
  left: 10px;
  bottom: 16px;
  width: 3px;
  border-radius: 999px;
  background: transparent;
}

.menu-item:hover,
.menu-item.is-active {
  transform: translateX(2px);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.12);
}

.menu-item.is-active {
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.08));
}

.menu-item.is-active::before {
  background: rgba(255, 255, 255, 0.86);
}

.menu-item__label {
  display: block;
  font-size: 15px;
  font-weight: 700;
}

.menu-item small {
  display: block;
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.5;
}

.app-main-shell {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.app-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 28px;
  border-bottom: 1px solid var(--line-soft);
  background: rgba(245, 248, 251, 0.86);
  backdrop-filter: blur(22px);
}

.app-topbar__left,
.app-topbar__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.app-topbar__eyebrow {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.app-topbar h2 {
  margin: 6px 0 4px;
  color: var(--ink-strong);
  font-size: 24px;
}

.app-topbar p {
  margin: 0;
  color: var(--ink-soft);
}

.user-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.user-block strong {
  color: var(--ink-strong);
}

.user-block span {
  color: var(--ink-soft);
  font-size: 13px;
}

.app-content {
  padding: 28px;
}

.nav-trigger {
  display: none;
}

.drawer-inner {
  padding: 20px;
}

.brand-panel--drawer {
  color: var(--ink-strong);
  background: var(--surface-soft);
  border-color: var(--line-soft);
}

.brand-panel--drawer p {
  color: var(--ink-soft);
}

.sidebar-summary--drawer {
  margin-bottom: 10px;
}

@media (max-width: 1100px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    display: none;
  }

  .nav-trigger {
    display: inline-flex;
  }
}

@media (max-width: 960px) {
  .app-topbar,
  .app-topbar__left,
  .app-topbar__right {
    align-items: flex-start;
  }

  .app-topbar {
    flex-direction: column;
    padding: 16px 20px;
  }

  .user-block {
    align-items: flex-start;
  }

  .app-content {
    padding: 20px;
  }
}
</style>
