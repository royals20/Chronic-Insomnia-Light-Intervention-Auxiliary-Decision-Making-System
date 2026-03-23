import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

import { hasAnyRole } from '@/auth/access';
import { pinia } from '@/stores';
import { useAuthStore } from '@/stores/auth';

const AdminLayout = () => import('@/layouts/AdminLayout.vue');
const CausalResultsView = () => import('@/views/CausalResultsView.vue');
const DashboardView = () => import('@/views/DashboardView.vue');
const DataCenterView = () => import('@/views/DataCenterView.vue');
const DataQualityView = () => import('@/views/DataQualityView.vue');
const ForbiddenView = () => import('@/views/ForbiddenView.vue');
const LoginView = () => import('@/views/LoginView.vue');
const ModelCenterView = () => import('@/views/ModelCenterView.vue');
const RecommendationCenterView = () => import('@/views/RecommendationCenterView.vue');
const ReportCenterView = () => import('@/views/ReportCenterView.vue');
const SubjectDetailView = () => import('@/views/SubjectDetailView.vue');
const SubjectListView = () => import('@/views/SubjectListView.vue');
const SubjectSectionEditorView = () => import('@/views/SubjectSectionEditorView.vue');
const SystemSettingsView = () => import('@/views/SystemSettingsView.vue');

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      guestOnly: true,
      title: '登录',
      description: '使用系统账号登录科研辅助决策平台。',
    },
  },
  {
    path: '/forbidden',
    component: AdminLayout,
    meta: {
      requiresAuth: true,
      title: '访问受限',
      description: '当前账号不具备访问该页面的角色权限。',
      allowedRoles: ['admin', 'researcher', 'data_entry'],
    },
    children: [
      {
        path: '',
        name: 'forbidden',
        component: ForbiddenView,
        meta: {
          requiresAuth: true,
          title: '访问受限',
          description: '当前账号不具备访问该页面的角色权限。',
          allowedRoles: ['admin', 'researcher', 'data_entry'],
        },
      },
    ],
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    meta: {
      requiresAuth: true,
      allowedRoles: ['admin', 'researcher', 'data_entry'],
    },
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardView,
        meta: {
          requiresAuth: true,
          title: '系统总览',
          description: '查看研究平台的运行概况、导入节奏与当前角色的关键入口。',
          allowedRoles: ['admin', 'researcher', 'data_entry'],
        },
      },
      {
        path: 'subjects',
        name: 'subjects',
        component: SubjectListView,
        meta: {
          requiresAuth: true,
          title: '受试者列表',
          description: '受试者档案、录入进度与筛选查询。',
          allowedRoles: ['admin', 'researcher', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id',
        name: 'subject-detail',
        component: SubjectDetailView,
        meta: {
          requiresAuth: true,
          title: '受试者详情',
          description: '查看单例受试者的完整档案与时间线。',
          allowedRoles: ['admin', 'researcher', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id/baseline',
        name: 'subject-baseline',
        component: SubjectSectionEditorView,
        meta: {
          requiresAuth: true,
          title: '基线特征录入',
          description: '编辑受试者基线数据。',
          sectionKey: 'baseline',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id/questionnaire',
        name: 'subject-questionnaire',
        component: SubjectSectionEditorView,
        meta: {
          requiresAuth: true,
          title: '量表录入',
          description: '编辑量表评分与评估时间。',
          sectionKey: 'questionnaire',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id/sleep',
        name: 'subject-sleep',
        component: SubjectSectionEditorView,
        meta: {
          requiresAuth: true,
          title: '睡眠指标录入',
          description: '编辑客观睡眠指标。',
          sectionKey: 'sleep',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id/light',
        name: 'subject-light',
        component: SubjectSectionEditorView,
        meta: {
          requiresAuth: true,
          title: '光干预录入',
          description: '编辑光干预方案与执行情况。',
          sectionKey: 'light',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'subjects/:id/followup',
        name: 'subject-followup',
        component: SubjectSectionEditorView,
        meta: {
          requiresAuth: true,
          title: '随访结局录入',
          description: '编辑主要和次要结局。',
          sectionKey: 'followup',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'data-center',
        name: 'data-center',
        component: DataCenterView,
        meta: {
          requiresAuth: true,
          title: '数据中心',
          description: '模板下载、数据导入、批次记录与问题样本聚焦。',
          allowedRoles: ['admin', 'data_entry'],
        },
      },
      {
        path: 'data-quality',
        name: 'data-quality',
        component: DataQualityView,
        meta: {
          requiresAuth: true,
          title: '数据质量',
          description: '查看阻塞问题、警告问题和修复建议。',
          allowedRoles: ['admin', 'researcher', 'data_entry'],
        },
      },
      {
        path: 'recommendation-center',
        name: 'recommendation-center',
        component: RecommendationCenterView,
        meta: {
          requiresAuth: true,
          title: '评估推荐',
          description: '执行规则评估、批量推荐与历史追溯。',
          allowedRoles: ['admin', 'researcher'],
        },
      },
      {
        path: 'report-center',
        name: 'report-center',
        component: ReportCenterView,
        meta: {
          requiresAuth: true,
          title: '报告中心',
          description: '查看单例报告与批量导出清单。',
          allowedRoles: ['admin', 'researcher'],
        },
      },
      {
        path: 'model-center',
        name: 'model-center',
        component: ModelCenterView,
        meta: {
          requiresAuth: true,
          title: '模型中心',
          description: '发起训练、激活版本并查看复现参数。',
          allowedRoles: ['admin', 'researcher'],
        },
      },
      {
        path: 'causal-results',
        name: 'causal-results',
        component: CausalResultsView,
        meta: {
          requiresAuth: true,
          title: '因果结果',
          description: '查看 ATE、特征贡献与亚组差异。',
          allowedRoles: ['admin', 'researcher'],
        },
      },
      {
        path: 'system-settings',
        name: 'system-settings',
        component: SystemSettingsView,
        meta: {
          requiresAuth: true,
          title: '系统设置',
          description: '管理推荐规则配置与系统用户。',
          allowedRoles: ['admin'],
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);

  if (to.meta.guestOnly) {
    const hasSession = await authStore.ensureSession();
    if (hasSession) {
      return '/dashboard';
    }
    return true;
  }

  if (to.meta.requiresAuth) {
    const hasSession = await authStore.ensureSession();
    if (!hasSession) {
      return {
        path: '/login',
        query: {
          redirect: to.fullPath,
        },
      };
    }

    if (to.meta.allowedRoles && !hasAnyRole(authStore.role, to.meta.allowedRoles)) {
      return {
        path: '/forbidden',
        query: {
          from: to.fullPath,
        },
      };
    }
  }

  if (to.meta.title) {
    document.title = `${to.meta.title} | 慢性失眠光干预科研平台`;
  }

  return true;
});

export default router;
