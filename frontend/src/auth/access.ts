export type UserRole = 'admin' | 'researcher' | 'data_entry';

export type Capability =
  | 'manage_users'
  | 'manage_system_settings'
  | 'view_subjects'
  | 'create_patient'
  | 'edit_patient'
  | 'delete_patient'
  | 'import_data'
  | 'view_data_quality'
  | 'evaluate_recommendations'
  | 'view_reports'
  | 'export_reports'
  | 'train_models'
  | 'activate_models';

export interface AppMenuItem {
  path: string;
  label: string;
  description: string;
  roles: UserRole[];
}

const capabilityMatrix: Record<UserRole, Capability[]> = {
  admin: [
    'manage_users',
    'manage_system_settings',
    'view_subjects',
    'create_patient',
    'edit_patient',
    'delete_patient',
    'import_data',
    'view_data_quality',
    'evaluate_recommendations',
    'view_reports',
    'export_reports',
    'train_models',
    'activate_models',
  ],
  researcher: [
    'view_subjects',
    'view_data_quality',
    'evaluate_recommendations',
    'view_reports',
    'export_reports',
    'train_models',
    'activate_models',
  ],
  data_entry: [
    'view_subjects',
    'create_patient',
    'edit_patient',
    'import_data',
    'view_data_quality',
  ],
};

export const appMenu: AppMenuItem[] = [
  {
    path: '/dashboard',
    label: '总览',
    description: '系统概况与关键指标',
    roles: ['admin', 'researcher', 'data_entry'],
  },
  {
    path: '/subjects',
    label: '受试者',
    description: '档案查看、录入与追踪',
    roles: ['admin', 'researcher', 'data_entry'],
  },
  {
    path: '/data-center',
    label: '数据中心',
    description: '模板下载、导入与批次记录',
    roles: ['admin', 'data_entry'],
  },
  {
    path: '/data-quality',
    label: '数据质量',
    description: '缺失、阻塞与修复建议',
    roles: ['admin', 'researcher', 'data_entry'],
  },
  {
    path: '/recommendation-center',
    label: '评估推荐',
    description: '规则评估与历史结果',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/report-center',
    label: '报告中心',
    description: '预览、打印与导出',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/model-center',
    label: '模型中心',
    description: '训练、版本与复现参数',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/causal-results',
    label: '因果结果',
    description: 'ATE、亚组与个体效应',
    roles: ['admin', 'researcher'],
  },
  {
    path: '/system-settings',
    label: '系统设置',
    description: '推荐规则与用户管理',
    roles: ['admin'],
  },
];

export function hasAnyRole(role: UserRole | null | undefined, roles?: UserRole[]) {
  if (!roles || roles.length === 0) {
    return true;
  }
  if (!role) {
    return false;
  }
  return roles.includes(role);
}

export function hasCapability(role: UserRole | null | undefined, capability: Capability) {
  if (!role) {
    return false;
  }
  return capabilityMatrix[role].includes(capability);
}

export function roleLabel(role: UserRole | null | undefined) {
  switch (role) {
    case 'admin':
      return '管理员';
    case 'researcher':
      return '研究员';
    case 'data_entry':
      return '录入员';
    default:
      return '未登录';
  }
}
