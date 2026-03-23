<template>
  <div class="page-stack">
    <DisclaimerBanner />

    <InsightHero
      eyebrow="Workspace Overview"
      title="科研决策驾驶舱总览"
      description="把数据导入、质量审阅、规则评估、因果训练和报告输出组织成一条可展示、可解释的科研链路。"
    >
      <template #meta>
        <DataBadge :label="roleLabel(authStore.role)" tone="primary" />
        <DataBadge label="权限已同步后端" tone="success" />
        <DataBadge label="仅供科研辅助" tone="warning" />
      </template>

      <template #actions>
        <ToolbarRow>
          <el-button type="primary" @click="goTo('/recommendation-center')">进入评估推荐</el-button>
          <el-button type="primary" plain @click="goTo('/subjects')">查看受试者库</el-button>
          <el-button v-if="authStore.can('train_models')" @click="goTo('/model-center')">进入模型中心</el-button>
        </ToolbarRow>
      </template>

      <template #aside>
        <div class="dashboard-hero-aside">
          <div class="key-value-grid">
            <div class="key-value-card">
              <span>当前角色</span>
              <strong>{{ roleLabel(authStore.role) }}</strong>
            </div>
            <div class="key-value-card">
              <span>开放模块</span>
              <strong>{{ enabledModuleCount }}</strong>
            </div>
          </div>
          <p class="dashboard-hero-aside__text">
            页面入口按角色实时裁剪，适合在答辩中直接说明“谁能做什么、当前流程走到哪里”。
          </p>
        </div>
      </template>
    </InsightHero>

    <InsightSummaryStrip :items="summaryItems" />

    <div class="page-grid two">
      <NarrativePanel title="最近 7 日导入趋势" description="用一张图说明数据积累节奏与平台活跃度。">
        <div ref="chartRef" class="chart-box"></div>
      </NarrativePanel>

      <NarrativePanel title="当前角色可执行动作" description="展示当前账号在系统中的职责边界和推荐入口。">
        <div class="capability-list">
          <div v-for="item in capabilitySummary" :key="item.title" class="capability-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
        </div>
      </NarrativePanel>
    </div>

    <NarrativePanel title="最近导入记录" description="按时间倒序展示最近的导入批次和样本数量。">
      <el-table :data="recentImports" stripe>
        <el-table-column prop="batchNo" label="批次编号" min-width="140" />
        <el-table-column prop="operator" label="操作人" min-width="100" />
        <el-table-column prop="importedAt" label="导入时间" min-width="170" />
        <el-table-column prop="count" label="病例数" width="90" />
      </el-table>
    </NarrativePanel>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { roleLabel } from '@/auth/access';
import DataBadge from '@/components/DataBadge.vue';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import InsightHero from '@/components/InsightHero.vue';
import InsightSummaryStrip from '@/components/InsightSummaryStrip.vue';
import NarrativePanel from '@/components/NarrativePanel.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const statistics = [
  {
    label: '受试者总数',
    value: 128,
    description: '当前纳入科研原型数据库的模拟样本。',
    tone: 'primary' as const,
  },
  {
    label: '已完成基线评估',
    value: 96,
    description: '已录入基线量表与核心睡眠信息。',
    tone: 'success' as const,
  },
  {
    label: '已生成推荐结果',
    value: 74,
    description: '已完成规则评估并形成推荐记录。',
    tone: 'warning' as const,
  },
];

const recentImports = [
  { batchNo: 'IMP-20260319-01', operator: '王研究员', importedAt: '2026-03-19 09:20', count: 12 },
  { batchNo: 'IMP-20260318-02', operator: '李录入员', importedAt: '2026-03-18 16:40', count: 18 },
  { batchNo: 'IMP-20260318-01', operator: '张管理员', importedAt: '2026-03-18 10:15', count: 9 },
  { batchNo: 'IMP-20260317-03', operator: '王研究员', importedAt: '2026-03-17 14:05', count: 21 },
];

const summaryItems = computed(() => statistics);

const capabilitySummary = computed(() => {
  if (authStore.role === 'admin') {
    return [
      { title: '系统治理', description: '用户管理、规则配置和所有业务操作均可执行。' },
      { title: '数据闭环', description: '支持导入、录入、删除、评估、报告和模型训练。' },
      { title: '答辩主账号', description: '适合作为论文汇报或系统管理演示入口。' },
    ];
  }

  if (authStore.role === 'researcher') {
    return [
      { title: '只读数据访问', description: '可浏览受试者与质量数据，但不修改录入内容。' },
      { title: '分析能力', description: '可执行规则评估、查看报告并训练和激活因果模型。' },
      { title: '重点入口', description: '推荐中心、报告中心、模型中心与因果结果页已开放。' },
    ];
  }

  return [
    { title: '数据录入优先', description: '可导入数据、创建受试者并维护五类录入表单。' },
    { title: '质量联动', description: '可查看数据质量页和问题样本，便于补录与修正。' },
    { title: '权限边界', description: '推荐、报告、模型与系统设置默认不可访问。' },
  ];
});

const enabledModuleCount = computed(() =>
  [
    authStore.can('view_subjects'),
    authStore.can('import_data'),
    authStore.can('view_data_quality'),
    authStore.can('evaluate_recommendations'),
    authStore.can('view_reports'),
    authStore.can('train_models'),
  ].filter(Boolean).length,
);

const chartRef = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

function goTo(path: string) {
  void router.push(path);
}

function resizeChart() {
  chart?.resize();
}

onMounted(() => {
  if (!chartRef.value) {
    return;
  }

  chart = echarts.init(chartRef.value);
  chart.setOption({
    color: ['#13718d'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(19, 42, 66, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff' },
    },
    grid: {
      left: 24,
      right: 16,
      top: 28,
      bottom: 24,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: ['03-13', '03-14', '03-15', '03-16', '03-17', '03-18', '03-19'],
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#c8d5e2' } },
      axisLabel: { color: '#6d8193' },
    },
    yAxis: {
      type: 'value',
      name: '导入人数',
      axisLabel: { color: '#6d8193' },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#dde7f0',
        },
      },
    },
    series: [
      {
        name: '导入病例数',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        data: [10, 12, 9, 15, 18, 21, 12],
        lineStyle: { width: 3, color: '#13718d' },
        itemStyle: { color: '#13718d' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(19, 113, 141, 0.34)' },
            { offset: 1, color: 'rgba(19, 113, 141, 0.04)' },
          ]),
        },
      },
    ],
  });

  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.dashboard-hero-aside {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    linear-gradient(180deg, rgba(13, 95, 111, 0.1), rgba(13, 95, 111, 0.03)),
    rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(13, 95, 111, 0.12);
}

.dashboard-hero-aside__text {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.chart-box {
  height: 360px;
}

.capability-list {
  display: grid;
  gap: 14px;
}

.capability-item {
  padding: 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: rgba(248, 251, 255, 0.76);
}

.capability-item strong {
  color: var(--ink-strong);
}

.capability-item p {
  margin: 8px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}
</style>
