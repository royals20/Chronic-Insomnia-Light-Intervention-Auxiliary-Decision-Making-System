import { createRouter, createWebHistory } from 'vue-router';

import AdminLayout from '@/layouts/AdminLayout.vue';
import CausalResultsView from '@/views/CausalResultsView.vue';
import DashboardView from '@/views/DashboardView.vue';
import DataCenterView from '@/views/DataCenterView.vue';
import DataQualityView from '@/views/DataQualityView.vue';
import LoginView from '@/views/LoginView.vue';
import ModelCenterView from '@/views/ModelCenterView.vue';
import RecommendationCenterView from '@/views/RecommendationCenterView.vue';
import ReportCenterView from '@/views/ReportCenterView.vue';
import SubjectDetailView from '@/views/SubjectDetailView.vue';
import SubjectListView from '@/views/SubjectListView.vue';
import SubjectSectionEditorView from '@/views/SubjectSectionEditorView.vue';
import SystemSettingsView from '@/views/SystemSettingsView.vue';
import { pinia } from '@/stores';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        guestOnly: true,
        title: '登录',
      },
    },
    {
      path: '/',
      component: AdminLayout,
      redirect: '/dashboard',
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: {
            requiresAuth: true,
            title: '首页概览',
          },
        },
        {
          path: 'subjects',
          name: 'subjects',
          component: SubjectListView,
          meta: {
            requiresAuth: true,
            title: '受试者列表',
          },
        },
        {
          path: 'subjects/:id',
          name: 'subject-detail',
          component: SubjectDetailView,
          meta: {
            requiresAuth: true,
            title: '受试者详情',
          },
        },
        {
          path: 'subjects/:id/baseline',
          name: 'subject-baseline',
          component: SubjectSectionEditorView,
          meta: {
            requiresAuth: true,
            title: '基线特征录入',
            sectionKey: 'baseline',
          },
        },
        {
          path: 'subjects/:id/questionnaire',
          name: 'subject-questionnaire',
          component: SubjectSectionEditorView,
          meta: {
            requiresAuth: true,
            title: '量表录入',
            sectionKey: 'questionnaire',
          },
        },
        {
          path: 'subjects/:id/sleep',
          name: 'subject-sleep',
          component: SubjectSectionEditorView,
          meta: {
            requiresAuth: true,
            title: '客观睡眠指标录入',
            sectionKey: 'sleep',
          },
        },
        {
          path: 'subjects/:id/light',
          name: 'subject-light',
          component: SubjectSectionEditorView,
          meta: {
            requiresAuth: true,
            title: '光干预记录',
            sectionKey: 'light',
          },
        },
        {
          path: 'subjects/:id/followup',
          name: 'subject-followup',
          component: SubjectSectionEditorView,
          meta: {
            requiresAuth: true,
            title: '随访结局录入',
            sectionKey: 'followup',
          },
        },
        {
          path: 'data-center',
          name: 'data-center',
          component: DataCenterView,
          meta: {
            requiresAuth: true,
            title: '数据中心',
          },
        },
        {
          path: 'data-quality',
          name: 'data-quality',
          component: DataQualityView,
          meta: {
            requiresAuth: true,
            title: '数据质量检查',
          },
        },
        {
          path: 'recommendation-center',
          name: 'recommendation-center',
          component: RecommendationCenterView,
          meta: {
            requiresAuth: true,
            title: '评估/推荐中心',
          },
        },
        {
          path: 'report-center',
          name: 'report-center',
          component: ReportCenterView,
          meta: {
            requiresAuth: true,
            title: '报告中心',
          },
        },
        {
          path: 'model-center',
          name: 'model-center',
          component: ModelCenterView,
          meta: {
            requiresAuth: true,
            title: '模型中心',
          },
        },
        {
          path: 'causal-results',
          name: 'causal-results',
          component: CausalResultsView,
          meta: {
            requiresAuth: true,
            title: '因果评估结果',
          },
        },
        {
          path: 'system-settings',
          name: 'system-settings',
          component: SystemSettingsView,
          meta: {
            requiresAuth: true,
            title: '系统设置',
          },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
});

router.beforeEach((to) => {
  const authStore = useAuthStore(pinia);

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return '/dashboard';
  }

  return true;
});

export default router;
