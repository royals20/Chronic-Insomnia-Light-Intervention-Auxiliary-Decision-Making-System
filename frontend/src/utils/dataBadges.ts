export type BadgeTone =
  | 'neutral'
  | 'primary'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger';

export interface BadgeDescriptor {
  label: string;
  tone: BadgeTone;
}

export function badgeForRecommendationLevel(level: string | null | undefined): BadgeDescriptor {
  switch (level) {
    case '推荐光干预':
      return { label: level, tone: 'success' };
    case '谨慎推荐并短期复评':
      return { label: level, tone: 'warning' };
    case '暂不直接推荐':
      return { label: level, tone: 'danger' };
    default:
      return { label: level || '未生成', tone: 'neutral' };
  }
}

export function badgeForReproducibility(status: string | null | undefined): BadgeDescriptor {
  switch (status) {
    case 'real_estimator':
      return { label: '真实估计器', tone: 'success' };
    case 'fallback_demo':
      return { label: 'Fallback 演示', tone: 'warning' };
    default:
      return { label: '状态未知', tone: 'neutral' };
  }
}

export function badgeForModelStatus(status: string | null | undefined): BadgeDescriptor {
  switch (status) {
    case 'active':
      return { label: '已激活', tone: 'success' };
    case 'archived':
      return { label: '已归档', tone: 'neutral' };
    case 'training':
      return { label: '训练中', tone: 'warning' };
    case 'failed':
      return { label: '训练失败', tone: 'danger' };
    default:
      return { label: status || '未标记', tone: 'neutral' };
  }
}

export function badgeForCompleteness(score: number | null | undefined): BadgeDescriptor {
  if (score === null || score === undefined) {
    return { label: '完整性未知', tone: 'neutral' };
  }
  if (score >= 85) {
    return { label: `完整性 ${score}`, tone: 'success' };
  }
  if (score >= 65) {
    return { label: `完整性 ${score}`, tone: 'warning' };
  }
  return { label: `完整性 ${score}`, tone: 'danger' };
}

export function badgeForDataReadiness(params: {
  blockingIssues: number;
  eligibleRecords?: number | null;
}): BadgeDescriptor {
  if (params.blockingIssues > 0) {
    return { label: `阻塞问题 ${params.blockingIssues}`, tone: 'danger' };
  }
  if ((params.eligibleRecords ?? 0) > 0) {
    return { label: '数据可训练', tone: 'success' };
  }
  return { label: '待补齐样本', tone: 'warning' };
}

export function badgeForPatientMaterialReady(ready: boolean): BadgeDescriptor {
  return ready
    ? { label: '资料较完整', tone: 'success' }
    : { label: '待补充资料', tone: 'warning' };
}
