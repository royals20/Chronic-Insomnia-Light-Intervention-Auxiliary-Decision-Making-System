<template>
  <div class="page-stack causal-results-page" v-loading="loading">
    <DisclaimerBanner />

    <InsightHero
      eyebrow="Causal Narrative"
      title="因果获益评估叙事页"
      description="先回答平均效应是否存在，再说明哪些特征在支撑结论、哪些亚组可能更敏感，以及当前结论适用于什么边界。"
    >
      <template #meta>
        <DataBadge
          :label="result ? badgeForReproducibility(result.reproducibility_status).label : '等待结果加载'"
          :tone="result ? badgeForReproducibility(result.reproducibility_status).tone : 'neutral'"
        />
        <DataBadge :label="result ? `有效样本 ${result.dataset_record_count}` : '请选择模型版本'" tone="primary" />
        <DataBadge label="仅供科研分析" tone="warning" />
      </template>

      <template #actions>
        <ToolbarRow>
          <el-select
            v-model="selectedModelVersionId"
            placeholder="请选择 causal 模型版本"
            filterable
            clearable
            class="model-select"
          >
            <el-option
              v-for="item in causalVersions"
              :key="item.id"
              :label="`${item.name} / ${item.status}`"
              :value="item.id"
            />
          </el-select>
          <el-button type="primary" @click="loadResult">加载结果</el-button>
          <el-button plain @click="goToModelCenter">返回模型中心</el-button>
        </ToolbarRow>
      </template>

      <template #aside>
        <div class="causal-hero-aside">
          <template v-if="result">
            <span class="causal-hero-aside__eyebrow">一句话结论</span>
            <h3>{{ causalConclusion }}</h3>
            <p>{{ result.estimator_message }}</p>
            <div class="tag-cluster">
              <DataBadge v-bind="badgeForModelStatus(result.model_version.status)" />
              <DataBadge v-bind="badgeForReproducibility(result.reproducibility_status)" />
            </div>
          </template>

          <EmptyState
            v-else
            badge="CAUSAL"
            title="尚未加载因果结果"
            description="选择一个已有产物的 causal 模型版本后，页面会展示总体结论、证据、亚组和样本示例。"
          />
        </div>
      </template>
    </InsightHero>

    <InsightSummaryStrip v-if="result" :items="resultSummaryItems" />

    <SectionNavRail
      v-if="result"
      :sections="sectionNavItems"
      :active-id="activeSectionId"
      @navigate="scrollToSection"
    />

    <template v-if="result">
      <section id="overview" class="story-section">
        <NarrativePanel title="总体结论" description="把平均处理效应、对照差值和一张宽版分布图放在同一屏，先讲总体判断。">
          <div class="overview-intro">
            <div class="result-highlight">
              <DataBadge v-bind="badgeForReproducibility(result.reproducibility_status)" />
              <h3>{{ causalConclusion }}</h3>
              <p>{{ counterfactualComparisonText }}</p>
            </div>

            <div class="key-value-grid">
              <div class="key-value-card">
                <span>ATE</span>
                <strong>{{ result.ate }}</strong>
              </div>
              <div class="key-value-card">
                <span>验证集 ATE</span>
                <strong>{{ result.validation_ate ?? '未填写' }}</strong>
              </div>
              <div class="key-value-card">
                <span>观察组间差值</span>
                <strong>{{ result.observed_group_difference ?? '未填写' }}</strong>
              </div>
            </div>
          </div>

          <div ref="distributionChartRef" class="chart-box chart-box--wide"></div>
        </NarrativePanel>
      </section>

      <section id="evidence" class="story-section">
        <div class="page-grid two">
          <NarrativePanel title="模型上下文" description="说明当前版本、处理定义、训练切分和特征选择，让结论具备可复现语境。">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="模型版本">
                {{ result.model_version.name }}
              </el-descriptions-item>
              <el-descriptions-item label="估计后端">
                {{ result.engine_backend }}
              </el-descriptions-item>
              <el-descriptions-item label="处理变量 T">
                {{ result.treatment_name }} vs {{ result.control_name }}
              </el-descriptions-item>
              <el-descriptions-item label="结局变量 Y">
                {{ result.outcome_name }}
              </el-descriptions-item>
              <el-descriptions-item label="训练集 / 验证集">
                {{ result.train_record_count }} / {{ result.validation_record_count }}
              </el-descriptions-item>
              <el-descriptions-item label="随机种子">
                {{ result.random_seed ?? '未记录' }}
              </el-descriptions-item>
              <el-descriptions-item label="验证集比例">
                {{ formatPercent(result.test_ratio) }}
              </el-descriptions-item>
              <el-descriptions-item label="最小覆盖率">
                {{ formatPercent(result.min_feature_coverage) }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="block">
              <div class="block__title">选中特征标签</div>
              <div class="tag-cluster">
                <DataBadge
                  v-for="item in result.selected_feature_names"
                  :key="item"
                  :label="item"
                  tone="primary"
                  size="sm"
                />
              </div>
            </div>
          </NarrativePanel>

          <NarrativePanel title="解释证据" description="通过特征重要性说明当前平均效应最可能由哪些变量结构支撑。">
            <div ref="importanceChartRef" class="chart-box"></div>
          </NarrativePanel>
        </div>
      </section>

      <section id="subgroups" class="story-section">
        <div class="page-grid two">
          <NarrativePanel title="人群差异" description="分层结果帮助说明哪些亚组更可能从当前处理策略中获益。">
            <div ref="subgroupChartRef" class="chart-box"></div>
          </NarrativePanel>

          <NarrativePanel title="亚组高亮" description="按平均 ITE 从高到低列出最值得在答辩中口头解释的亚组。">
            <div class="subgroup-highlight-list">
              <div v-for="item in subgroupHighlights" :key="item.key" class="subgroup-highlight-item">
                <div>
                  <strong>{{ item.label }}</strong>
                  <p>{{ item.description }}</p>
                </div>
                <DataBadge :label="`平均 ITE ${item.value}`" :tone="item.value >= 0 ? 'success' : 'danger'" />
              </div>
            </div>
          </NarrativePanel>
        </div>
      </section>

      <section id="samples" class="story-section">
        <div class="page-grid two">
          <NarrativePanel title="潜在高获益个体" description="适合说明哪些样本最有可能从当前处理策略中受益。">
            <el-table :data="result.top_positive_patients" stripe>
              <el-table-column prop="patient_code" label="患者编号" min-width="120" />
              <el-table-column prop="treatment_label" label="当前处理组" min-width="140" />
              <el-table-column prop="observed_outcome" label="观察结局" width="100" />
              <el-table-column prop="estimated_ite" label="估计 ITE" width="100" />
            </el-table>
          </NarrativePanel>

          <NarrativePanel title="潜在低获益个体" description="可用于解释为什么并非所有样本都应接受相同干预策略。">
            <el-table :data="result.top_negative_patients" stripe>
              <el-table-column prop="patient_code" label="患者编号" min-width="120" />
              <el-table-column prop="treatment_label" label="当前处理组" min-width="140" />
              <el-table-column prop="observed_outcome" label="观察结局" width="100" />
              <el-table-column prop="estimated_ite" label="估计 ITE" width="100" />
            </el-table>
          </NarrativePanel>
        </div>
      </section>

      <section id="limitations" class="story-section">
        <div class="page-grid two">
          <NarrativePanel title="适用前提" description="答辩时先讲当前结果在哪些前提下有解释价值。">
            <ul class="plain-list">
              <li v-for="item in result.assumptions" :key="item">{{ item }}</li>
            </ul>
          </NarrativePanel>

          <NarrativePanel title="局限性" description="最后收束到局限性，说明为什么当前结果是科研分析结论，而不是临床指令。">
            <ul class="plain-list">
              <li v-for="item in result.limitations" :key="item">{{ item }}</li>
            </ul>
          </NarrativePanel>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import DataBadge from '@/components/DataBadge.vue';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import EmptyState from '@/components/EmptyState.vue';
import InsightHero from '@/components/InsightHero.vue';
import InsightSummaryStrip from '@/components/InsightSummaryStrip.vue';
import NarrativePanel from '@/components/NarrativePanel.vue';
import SectionNavRail from '@/components/SectionNavRail.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import {
  fetchCausalResults,
  fetchModelVersions,
  type CausalEvaluationResultResponse,
  type ModelVersionSummary,
} from '@/api/modelCenter';
import {
  badgeForModelStatus,
  badgeForReproducibility,
} from '@/utils/dataBadges';
import { formatDateTime } from '@/utils/format';

const route = useRoute();
const router = useRouter();
const causalVersions = ref<ModelVersionSummary[]>([]);
const selectedModelVersionId = ref<number | undefined>();
const result = ref<CausalEvaluationResultResponse | null>(null);
const loading = ref(false);
const distributionChartRef = ref<HTMLElement | null>(null);
const importanceChartRef = ref<HTMLElement | null>(null);
const subgroupChartRef = ref<HTMLElement | null>(null);
const activeSectionId = ref('overview');
let distributionChart: echarts.ECharts | null = null;
let importanceChart: echarts.ECharts | null = null;
let subgroupChart: echarts.ECharts | null = null;

const sectionNavItems = [
  { id: 'overview', label: '总体结论', caption: 'ATE 与分布' },
  { id: 'evidence', label: '解释证据', caption: '模型语境与特征' },
  { id: 'subgroups', label: '人群差异', caption: '亚组结果' },
  { id: 'samples', label: '样本示例', caption: '高获益与低获益' },
  { id: 'limitations', label: '局限性', caption: '适用前提与边界' },
];

const resultSummaryItems = computed(() => {
  if (!result.value) {
    return [];
  }
  return [
    {
      label: 'ATE',
      value: result.value.ate,
      description: '整体平均处理效应。',
      tone: result.value.ate >= 0 ? ('success' as const) : ('danger' as const),
    },
    {
      label: '验证集 ATE',
      value: result.value.validation_ate ?? '未填写',
      description: '验证集上的平均效应估计。',
      tone: 'primary' as const,
    },
    {
      label: '观察组差值',
      value: result.value.observed_group_difference ?? '未填写',
      description: '未调整混杂时的处理组差值。',
      tone: 'warning' as const,
    },
    {
      label: '有效样本',
      value: result.value.dataset_record_count,
      description: '参与本次因果分析的记录数。',
      tone: 'info' as const,
    },
  ];
});

const causalConclusion = computed(() => {
  if (!result.value) {
    return '请先加载模型结果';
  }
  if (result.value.ate > 0) {
    return `当前模型提示 ${result.value.treatment_name} 相对 ${result.value.control_name} 呈正向平均效应`;
  }
  if (result.value.ate < 0) {
    return `当前模型未显示 ${result.value.treatment_name} 相对 ${result.value.control_name} 的正向平均效应`;
  }
  return '当前模型显示两组平均效应差异接近于零';
});

const counterfactualComparisonText = computed(() => {
  if (!result.value) {
    return '';
  }
  return `针对结局变量“${result.value.outcome_name}”，当前模型估计的平均处理效应为 ${result.value.ate}，观察组间原始差值为 ${result.value.observed_group_difference ?? '未记录'}。`;
});

const subgroupHighlights = computed(() => {
  if (!result.value) {
    return [];
  }
  return [...result.value.subgroup_results]
    .sort((left, right) => right.average_ite - left.average_ite)
    .slice(0, 4)
    .map((item) => ({
      key: `${item.feature_name}-${item.subgroup_name}`,
      label: `${item.feature_label} / ${item.subgroup_name}`,
      description: `样本数 ${item.sample_count}，该亚组平均 ITE 为 ${item.average_ite}。`,
      value: item.average_ite,
    }));
});

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '未记录';
  }
  return value <= 1 ? `${Math.round(value * 100)}%` : String(value);
}

function renderCharts() {
  if (!result.value || !distributionChartRef.value || !importanceChartRef.value || !subgroupChartRef.value) {
    return;
  }

  distributionChart ??= echarts.init(distributionChartRef.value);
  importanceChart ??= echarts.init(importanceChartRef.value);
  subgroupChart ??= echarts.init(subgroupChartRef.value);

  distributionChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 46, right: 20, top: 26, bottom: 42 },
    xAxis: {
      type: 'category',
      data: result.value.ite_distribution.map((item) => item.name),
      axisLabel: { interval: 0, rotate: 16 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'bar',
        data: result.value.ite_distribution.map((item) => item.value),
        itemStyle: { color: '#13718d', borderRadius: [8, 8, 0, 0] },
      },
    ],
  });

  importanceChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 110, right: 20, top: 20, bottom: 20 },
    xAxis: { type: 'value', name: '重要性' },
    yAxis: {
      type: 'category',
      data: result.value.feature_importance.map((item) => item.feature_label).reverse(),
    },
    series: [
      {
        type: 'bar',
        data: result.value.feature_importance.map((item) => item.importance).reverse(),
        itemStyle: { color: '#1d6b52', borderRadius: [0, 8, 8, 0] },
      },
    ],
  });

  subgroupChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 70 },
    xAxis: {
      type: 'category',
      data: result.value.subgroup_results.map((item) => `${item.feature_label}-${item.subgroup_name}`),
      axisLabel: { interval: 0, rotate: 26 },
    },
    yAxis: { type: 'value', name: '平均 ITE' },
    series: [
      {
        type: 'bar',
        data: result.value.subgroup_results.map((item) => item.average_ite),
        itemStyle: { color: '#9b6c2f', borderRadius: [8, 8, 0, 0] },
      },
    ],
  });
}

function resizeCharts() {
  distributionChart?.resize();
  importanceChart?.resize();
  subgroupChart?.resize();
}

function syncActiveSection() {
  if (!result.value) {
    return;
  }

  const topOffset = 160;
  let current = sectionNavItems[0].id;

  for (const item of sectionNavItems) {
    const element = document.getElementById(item.id);
    if (!element) {
      continue;
    }

    if (element.getBoundingClientRect().top - topOffset <= 0) {
      current = item.id;
    }
  }

  activeSectionId.value = current;
}

function scrollToSection(id: string) {
  activeSectionId.value = id;
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadVersions() {
  causalVersions.value = await fetchModelVersions('causal');
  const queryModelVersionId = Number(route.query.modelVersionId);
  if (!Number.isNaN(queryModelVersionId) && queryModelVersionId > 0) {
    selectedModelVersionId.value = queryModelVersionId;
    return;
  }
  const activeItem = causalVersions.value.find((item) => item.status === 'active' && item.artifact_path);
  const firstAvailable = causalVersions.value.find((item) => item.artifact_path);
  selectedModelVersionId.value = activeItem?.id || firstAvailable?.id;
}

async function loadResult() {
  loading.value = true;
  try {
    result.value = await fetchCausalResults(selectedModelVersionId.value);
    activeSectionId.value = 'overview';
    await nextTick();
    renderCharts();
    syncActiveSection();
  } catch (error) {
    result.value = null;
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function goToModelCenter() {
  void router.push('/model-center');
}

onMounted(async () => {
  await loadVersions();
  if (selectedModelVersionId.value) {
    await loadResult();
  }
  window.addEventListener('resize', resizeCharts);
  window.addEventListener('scroll', syncActiveSection, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts);
  window.removeEventListener('scroll', syncActiveSection);
  distributionChart?.dispose();
  importanceChart?.dispose();
  subgroupChart?.dispose();
});
</script>

<style scoped>
.model-select {
  width: 360px;
}

.causal-hero-aside {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    linear-gradient(180deg, rgba(13, 95, 111, 0.08), rgba(13, 95, 111, 0.03)),
    rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(13, 95, 111, 0.1);
}

.causal-hero-aside__eyebrow,
.block__title {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.causal-hero-aside h3 {
  margin: 0;
  color: var(--ink-strong);
  font-size: 28px;
  line-height: 1.08;
}

.causal-hero-aside p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.story-section {
  scroll-margin-top: 160px;
}

.overview-intro {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  margin-bottom: 18px;
}

.result-highlight {
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top right, rgba(13, 95, 111, 0.14), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 248, 250, 0.94));
  border: 1px solid rgba(13, 95, 111, 0.12);
}

.result-highlight h3 {
  margin: 16px 0 10px;
  color: var(--ink-strong);
  font-size: clamp(28px, 2.4vw, 38px);
  line-height: 1.08;
}

.result-highlight p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.chart-box {
  height: 340px;
}

.chart-box--wide {
  height: 380px;
}

.block {
  margin-top: 18px;
}

.subgroup-highlight-list {
  display: grid;
  gap: 14px;
}

.subgroup-highlight-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: rgba(248, 251, 255, 0.78);
}

.subgroup-highlight-item strong {
  color: var(--ink-strong);
}

.subgroup-highlight-item p {
  margin: 8px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

@media (max-width: 960px) {
  .model-select {
    width: 100%;
  }

  .overview-intro {
    grid-template-columns: 1fr;
  }

  .subgroup-highlight-item {
    flex-direction: column;
  }
}
</style>
