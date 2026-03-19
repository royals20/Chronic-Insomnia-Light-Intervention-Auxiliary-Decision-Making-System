<template>
  <el-container class="app-shell">
    <el-aside class="app-aside" width="240px">
      <div class="brand-block">
        <h1>科研辅助决策系统</h1>
        <p>慢性失眠光干预原型平台</p>
      </div>
      <el-menu :default-active="activeMenu" router class="side-menu">
        <el-menu-item index="/dashboard">首页概览</el-menu-item>
        <el-menu-item index="/subjects">受试者管理</el-menu-item>
        <el-menu-item index="/data-center">数据中心</el-menu-item>
        <el-menu-item index="/data-quality">数据质量检查</el-menu-item>
        <el-menu-item index="/recommendation-center">评估/推荐中心</el-menu-item>
        <el-menu-item index="/report-center">报告中心</el-menu-item>
        <el-menu-item index="/model-center">模型中心</el-menu-item>
        <el-menu-item index="/causal-results">因果评估结果</el-menu-item>
        <el-menu-item index="/system-settings">系统设置</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <h2>{{ pageTitle }}</h2>
          <p>仅供科研辅助，不替代临床诊断与治疗</p>
        </div>
        <div class="header-actions">
          <span class="user-name">{{ authStore.user?.full_name || '未登录用户' }}</span>
          <el-button type="primary" plain @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const pageTitle = computed(() => {
  return (route.meta.title as string | undefined) || '后台首页';
});

const menuPrefixes = [
  '/subjects',
  '/data-quality',
  '/data-center',
  '/recommendation-center',
  '/report-center',
  '/model-center',
  '/causal-results',
  '/system-settings',
];

const activeMenu = computed(() => {
  const matched = menuPrefixes.find((prefix) => route.path.startsWith(prefix));
  return matched || '/dashboard';
});

function handleLogout() {
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-aside {
  background: linear-gradient(180deg, #123c65 0%, #0d2840 100%);
  color: #fff;
}

.brand-block {
  padding: 28px 20px 16px;
}

.brand-block h1 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
}

.brand-block p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  line-height: 1.6;
}

.side-menu {
  border-right: none;
  background: transparent;
}

:deep(.side-menu .el-menu-item) {
  color: rgba(255, 255, 255, 0.78);
}

:deep(.side-menu .el-menu-item.is-active) {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  height: auto;
  background: #fff;
  border-bottom: 1px solid #e8edf3;
}

.app-header h2 {
  margin: 0 0 6px;
  font-size: 24px;
  color: #16324f;
}

.app-header p {
  margin: 0;
  color: #6b7b8d;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  color: #35506c;
  font-size: 14px;
}

.app-main {
  background: #f3f6fb;
  padding: 24px 28px;
}

@media (max-width: 960px) {
  .app-shell {
    flex-direction: column;
  }

  .app-aside {
    width: 100% !important;
  }

  .app-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
