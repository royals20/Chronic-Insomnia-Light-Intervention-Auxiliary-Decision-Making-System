<template>
  <div class="page-stack">
    <DisclaimerBanner />

    <InsightHero
      eyebrow="Model Lab"
      title="因果训练驾驶舱"
      description="把当前激活模型、样本准备度、训练参数和版本复现关系压缩到首屏，答辩时先讲清“现在能不能训、训完会产出什么”。"
    >
      <template #meta>
        <DataBadge v-bind="activeModelReproBadge" />
        <DataBadge v-bind="dataReadinessBadge" />
        <DataBadge
          :label="`待修复样本 ${qualitySummary?.summary.affected_patient_count ?? 0}`"
          :tone="(qualitySummary?.summary.affected_patient_count ?? 0) > 0 ? 'warning' : 'success'"
        />
      </template>

      <template #actions>
        <ToolbarRow>
          <el-button type="primary" @click="handleTrain" :loading="trainingLoading">发起训练</el-button>
          <el-button type="primary" plain @click="refreshAll">刷新概览</el-button>
          <el-button @click="goToQualityPage">查看质量页</el-button>
        </ToolbarRow>
      </template>

      <template #aside>
        <div class="model-hero-aside">
          <template v-if="activeModel">
            <span class="model-hero-aside__eyebrow">当前激活模型</span>
            <h3>{{ activeModel.name }}</h3>
            <p>{{ activeModel.description || '当前激活版本暂无额外说明。' }}</p>
            <div class="tag-cluster">
              <DataBadge v-bind="badgeForModelStatus(activeModel.status)" />
              <DataBadge v-bind="badgeForReproducibility(activeModel.reproducibility_status)" />
            </div>
          </template>

          <EmptyState
            v-else
            badge="MODEL"
            title="当前没有激活的 causal 模型"
            description="训练并激活一个版本后，这里会显示默认模型与复现状态。"
          />
        </div>
      </template>
    </InsightHero>

    <InsightSummaryStrip :items="summaryItems" />

    <div class="page-grid two">
      <NarrativePanel title="训练控制台" description="固定随机种子、验证集比例和特征覆盖率，确保每次实验都能复用与对比。">
        <el-form label-position="top">
          <el-form-item label="模型名称">
            <el-input v-model="trainForm.model_name" placeholder="为空时自动生成版本名" />
          </el-form-item>

          <div class="compact-grid">
            <el-form-item label="验证集比例">
              <el-input-number v-model="trainForm.test_ratio" :min="0.1" :max="0.4" :step="0.05" class="full-width" />
            </el-form-item>
            <el-form-item label="随机种子">
              <el-input-number v-model="trainForm.random_seed" :min="1" :max="99999999" class="full-width" />
            </el-form-item>
            <el-form-item label="最大特征数">
              <el-input-number v-model="trainForm.max_features" :min="4" :max="16" class="full-width" />
            </el-form-item>
            <el-form-item label="最小覆盖率">
              <el-input-number v-model="trainForm.min_feature_coverage" :min="0.3" :max="1" :step="0.05" class="full-width" />
            </el-form-item>
          </div>

          <el-form-item label="自定义特征名（逗号分隔，可选）">
            <el-input v-model="featureNamesText" placeholder="例如 age,psqi_score,isi_score,sleep_efficiency" />
          </el-form-item>

          <el-form-item label="训练后自动激活">
            <el-switch v-model="trainForm.activate_after_train" />
          </el-form-item>
        </el-form>

        <template #footer>
          <ToolbarRow>
            <el-button type="primary" :loading="trainingLoading" @click="handleTrain">发起训练</el-button>
            <el-button plain @click="refreshAll">刷新概览</el-button>
          </ToolbarRow>
        </template>
      </NarrativePanel>

      <NarrativePanel
        title="数据准备度"
        description="把能否训练、处理定义、结果变量和主要阻塞问题集中到一张叙事面板里。"
        tone="accent"
      >
        <template v-if="overview">
          <div class="key-value-grid">
            <div class="key-value-card">
              <span>处理变量 T</span>
              <strong>{{ `${overview.treatment_name} vs ${overview.control_name}` }}</strong>
            </div>
            <div class="key-value-card">
              <span>结局变量 Y</span>
              <strong>{{ overview.outcome_name }}</strong>
            </div>
            <div class="key-value-card">
              <span>结局范围</span>
              <strong>{{ outcomeRangeText }}</strong>
            </div>
          </div>

          <div class="block">
            <div class="block__title">自动选中特征</div>
            <div class="tag-cluster">
              <DataBadge
                v-for="item in overview.selected_feature_names"
                :key="item"
                :label="item"
                tone="primary"
                size="sm"
              />
            </div>
          </div>

          <div class="block">
            <div class="block__title">当前训练提示</div>
            <p class="subtle-text">{{ trainHintText }}</p>
            <ul class="plain-list">
              <li v-if="qualitySummary && qualitySummary.summary.blocking_issue_count > 0">
                当前存在 {{ qualitySummary.summary.blocking_issue_count }} 条阻塞性数据问题，建议先补录后训练。
              </li>
              <li v-if="overview.dropped_examples.length > 0">
                示例丢弃样本：{{ overview.dropped_examples.slice(0, 3).join('、') }}
              </li>
              <li v-if="overview.assumptions.length > 0">
                当前训练默认依赖清晰的 X / T / Y 定义与足够样本覆盖。
              </li>
            </ul>
          </div>
        </template>

        <EmptyState
          v-else
          badge="DATASET"
          title="数据集概览尚未加载"
          description="刷新后会展示处理定义、结果范围和自动选中特征。"
        />
      </NarrativePanel>
    </div>

    <div class="page-grid two">
      <NarrativePanel
        title="最新训练结果摘要"
        description="训练成功后，直接给出结论性指标并提供跳转到因果结果页的主入口。"
        tone="accent"
      >
        <template v-if="latestTraining">
          <div class="training-result-highlight">
            <DataBadge v-bind="badgeForReproducibility(latestTraining.result.reproducibility_status)" />
            <h3>{{ latestTraining.model_version.name }}</h3>
            <p>{{ latestTraining.result.estimator_message }}</p>
          </div>

          <div class="key-value-grid top-gap">
            <div class="key-value-card">
              <span>ATE</span>
              <strong>{{ latestTraining.result.ate }}</strong>
            </div>
            <div class="key-value-card">
              <span>验证集 ATE</span>
              <strong>{{ latestTraining.result.validation_ate ?? '未填充' }}</strong>
            </div>
            <div class="key-value-card">
              <span>有效样本</span>
              <strong>{{ latestTraining.result.dataset_record_count }}</strong>
            </div>
          </div>
        </template>

        <EmptyState
          v-else
          badge="TRAIN"
          title="尚未发起新的训练任务"
          description="训练完成后，这里会展示当前结论、关键指标和因果结果入口。"
        />

        <template #footer>
          <ToolbarRow v-if="latestTraining">
            <el-button type="primary" plain @click="goToCausalResult(latestTraining.model_version.id)">查看因果结果页</el-button>
          </ToolbarRow>
        </template>
      </NarrativePanel>

      <NarrativePanel title="处理组分布与特征视角" description="训练前先确认样本是否均衡，以及当前版本主要依赖哪些特征。">
        <template v-if="overview">
          <el-table :data="overview.treatment_distribution" stripe>
            <el-table-column prop="name" label="分组" min-width="180" />
            <el-table-column prop="value" label="样本数" width="100" />
          </el-table>

          <div class="block">
            <div class="block__title">前 6 个候选特征</div>
            <div class="tag-cluster">
              <DataBadge
                v-for="item in overview.selected_feature_names.slice(0, 6)"
                :key="item"
                :label="item"
                tone="info"
                size="sm"
              />
            </div>
          </div>
        </template>
      </NarrativePanel>
    </div>

    <NarrativePanel title="模型版本列表" description="版本状态、复现状态和关键参数统一放在同一张表中，便于横向解释实验差异。">
      <el-table :data="versions" stripe v-loading="versionsLoading">
        <el-table-column prop="name" label="版本名称" min-width="180" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <DataBadge v-bind="badgeForModelStatus(row.status)" size="sm" />
          </template>
        </el-table-column>
        <el-table-column label="复现状态" min-width="130">
          <template #default="{ row }">
            <DataBadge v-bind="badgeForReproducibility(row.reproducibility_status)" size="sm" />
          </template>
        </el-table-column>
        <el-table-column prop="engine_backend" label="估计后端" min-width="170" />
        <el-table-column label="关键参数" min-width="240">
          <template #default="{ row }">
            {{ `seed=${row.random_seed ?? '-'} / test=${formatPercent(row.test_ratio)} / cov=${formatPercent(row.min_feature_coverage)}` }}
          </template>
        </el-table-column>
        <el-table-column label="训练完成时间" min-width="190">
          <template #default="{ row }">{{ formatDateTime(row.training_completed_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="300">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button text type="primary" :disabled="row.status === 'active'" @click="handleActivate(row.id)">设为激活</el-button>
              <el-button text type="primary" :disabled="!row.artifact_path" @click="goToCausalResult(row.id)">查看结果</el-button>
              <el-button text type="primary" @click="handleReuseConfig(row)">复用配置</el-button>
              <el-button text type="primary" @click="handleRetrain(row)">按此配置重训</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </NarrativePanel>

    <NarrativePanel id="model-compare" title="版本对比" description="选择两个版本后，会持续显示当前比较态并并排展示关键指标差异。">
      <ToolbarRow>
        <el-select
          v-model="compareVersionIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择 2 个模型版本进行对比"
          class="full-width"
        >
          <el-option
            v-for="item in versions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </ToolbarRow>

      <div v-if="comparisonModels.length > 0" class="compare-selection-strip">
        <DataBadge
          v-for="item in comparisonModels"
          :key="item.id"
          :label="item.name"
          tone="primary"
        />
      </div>

      <el-table v-if="comparisonRows.length > 0 && comparisonModels.length === 2" :data="comparisonRows" stripe class="top-gap">
        <el-table-column prop="label" label="指标" min-width="180" />
        <el-table-column :label="comparisonModels[0].name" prop="left" min-width="220" />
        <el-table-column :label="comparisonModels[1].name" prop="right" min-width="220" />
      </el-table>

      <EmptyState
        v-else
        badge="COMPARE"
        title="请选择两个版本"
        description="这里会并排展示 ATE、验证集效果、随机种子和特征集差异。"
      />
    </NarrativePanel>

    <div v-if="compareVersionIds.length > 0" class="sticky-bottom-bar">
      <div class="sticky-bottom-bar__content">
        <div>
          <strong class="sticky-bottom-bar__title">当前比较态</strong>
          <p class="sticky-bottom-bar__text">
            已选 {{ compareVersionIds.length }} 个版本{{ comparisonModels.length > 0 ? `：${comparisonModels.map((item) => item.name).join(' / ')}` : '' }}
          </p>
        </div>

        <ToolbarRow>
          <el-button type="primary" plain @click="scrollToCompare">查看对比区</el-button>
          <el-button plain @click="compareVersionIds = []">清空选择</el-button>
        </ToolbarRow>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import type { DataQualityResponse } from '@/api/subjects';
import { fetchQualitySummary } from '@/api/subjects';
import DataBadge from '@/components/DataBadge.vue';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import EmptyState from '@/components/EmptyState.vue';
import InsightHero from '@/components/InsightHero.vue';
import InsightSummaryStrip from '@/components/InsightSummaryStrip.vue';
import NarrativePanel from '@/components/NarrativePanel.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import {
  activateModelVersion,
  fetchActiveModel,
  fetchCausalDatasetOverview,
  fetchModelVersions,
  trainCausalModel,
  type CausalTrainingRequest,
  type CausalTrainingResponse,
  type DatasetOverviewResponse,
  type ModelVersionSummary,
} from '@/api/modelCenter';
import {
  badgeForDataReadiness,
  badgeForModelStatus,
  badgeForReproducibility,
} from '@/utils/dataBadges';
import { formatDateTime } from '@/utils/format';

const router = useRouter();
const overview = ref<DatasetOverviewResponse | null>(null);
const activeModel = ref<ModelVersionSummary | null>(null);
const versions = ref<ModelVersionSummary[]>([]);
const latestTraining = ref<CausalTrainingResponse | null>(null);
const qualitySummary = ref<DataQualityResponse | null>(null);
const overviewLoading = ref(false);
const versionsLoading = ref(false);
const trainingLoading = ref(false);
const featureNamesText = ref('');
const compareVersionIds = ref<number[]>([]);
const trainForm = reactive({
  model_name: '',
  test_ratio: 0.2,
  random_seed: 20260319,
  max_features: 10,
  min_feature_coverage: 0.7,
  activate_after_train: true,
});

const outcomeRangeText = computed(() => {
  if (!overview.value?.outcome_summary) {
    return '未填充';
  }
  return `${overview.value.outcome_summary.min_value} ~ ${overview.value.outcome_summary.max_value}`;
});

const comparisonModels = computed(() =>
  versions.value.filter((item) => compareVersionIds.value.includes(item.id)).slice(0, 2),
);

const comparisonRows = computed(() => {
  if (comparisonModels.value.length !== 2) {
    return [];
  }
  const [left, right] = comparisonModels.value;
  return [
    { label: 'ATE', left: displayMetric(left.metrics.ate), right: displayMetric(right.metrics.ate) },
    { label: '验证集 ATE', left: displayMetric(left.metrics.validation_ate), right: displayMetric(right.metrics.validation_ate) },
    { label: '训练记录数', left: displayMetric(left.metrics.train_record_count), right: displayMetric(right.metrics.train_record_count) },
    { label: '验证记录数', left: displayMetric(left.metrics.validation_record_count), right: displayMetric(right.metrics.validation_record_count) },
    { label: '随机种子', left: left.random_seed ?? '未记录', right: right.random_seed ?? '未记录' },
    { label: '验证集比例', left: formatPercent(left.test_ratio), right: formatPercent(right.test_ratio) },
    { label: '最小覆盖率', left: formatPercent(left.min_feature_coverage), right: formatPercent(right.min_feature_coverage) },
    { label: '复现状态', left: badgeForReproducibility(left.reproducibility_status).label, right: badgeForReproducibility(right.reproducibility_status).label },
    { label: '选中特征', left: left.selected_feature_keys.join(', ') || '未记录', right: right.selected_feature_keys.join(', ') || '未记录' },
  ];
});

const activeModelReproBadge = computed(() => badgeForReproducibility(activeModel.value?.reproducibility_status));

const dataReadinessBadge = computed(() =>
  badgeForDataReadiness({
    blockingIssues: qualitySummary.value?.summary.blocking_issue_count ?? 0,
    eligibleRecords: overview.value?.eligible_records ?? 0,
  }),
);

const summaryItems = computed(() => [
  {
    label: '总样本数',
    value: overview.value?.total_patients ?? 0,
    description: '数据库中的全部受试者。',
    tone: 'primary' as const,
  },
  {
    label: '可建模记录',
    value: overview.value?.eligible_records ?? 0,
    description: '满足 T / Y 与协变量要求的样本。',
    tone: 'success' as const,
  },
  {
    label: '丢弃记录',
    value: overview.value?.dropped_records ?? 0,
    description: '因缺失或覆盖率不足未进入训练的样本。',
    tone: 'warning' as const,
  },
  {
    label: '阻塞问题',
    value: qualitySummary.value?.summary.blocking_issue_count ?? 0,
    description: '训练前应优先处理的数据问题。',
    tone: (qualitySummary.value?.summary.blocking_issue_count ?? 0) > 0 ? ('danger' as const) : ('neutral' as const),
  },
]);

const trainHintText = computed(() => {
  if (activeModel.value?.reproducibility_status === 'real_estimator') {
    return '当前环境可使用真实估计器，建议固定随机种子与覆盖率阈值，便于后续复现实验。';
  }
  return '如果环境缺少真实因果依赖，系统会自动降级到 fallback 演示估计器，并明确标记复现状态。';
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

function displayMetric(value: unknown) {
  return value ?? '未记录';
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return '未记录';
  }
  return value <= 1 ? `${Math.round(value * 100)}%` : String(value);
}

function buildTrainPayload(modelNameOverride?: string): CausalTrainingRequest {
  const featureNames = featureNamesText.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    model_name: modelNameOverride || trainForm.model_name || undefined,
    test_ratio: trainForm.test_ratio,
    random_seed: trainForm.random_seed,
    max_features: trainForm.max_features,
    min_feature_coverage: trainForm.min_feature_coverage,
    feature_names: featureNames.length > 0 ? featureNames : undefined,
    activate_after_train: trainForm.activate_after_train,
  };
}

function buildRerunName(sourceName: string) {
  const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 12);
  return `${sourceName}-重训-${stamp}`;
}

function applyVersionConfig(version: ModelVersionSummary, withModelName = true) {
  trainForm.test_ratio = version.test_ratio ?? 0.2;
  trainForm.random_seed = version.random_seed ?? 20260319;
  trainForm.max_features = Number(version.config.max_features ?? 10);
  trainForm.min_feature_coverage = version.min_feature_coverage ?? 0.7;
  trainForm.activate_after_train = true;
  trainForm.model_name = withModelName ? version.name : '';
  featureNamesText.value = version.selected_feature_keys.join(',');
}

async function runTraining(modelNameOverride?: string) {
  trainingLoading.value = true;
  try {
    latestTraining.value = await trainCausalModel(buildTrainPayload(modelNameOverride));
    ElMessage.success(latestTraining.value.message);
    await refreshAll();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    trainingLoading.value = false;
  }
}

async function loadOverview() {
  overviewLoading.value = true;
  try {
    overview.value = await fetchCausalDatasetOverview({
      max_features: trainForm.max_features,
      min_feature_coverage: trainForm.min_feature_coverage,
    });
  } finally {
    overviewLoading.value = false;
  }
}

async function loadVersions() {
  versionsLoading.value = true;
  try {
    versions.value = await fetchModelVersions('causal');
  } finally {
    versionsLoading.value = false;
  }
}

async function loadActiveModel() {
  const data = await fetchActiveModel('causal');
  activeModel.value = data.active_model;
}

async function loadQualitySummary() {
  qualitySummary.value = await fetchQualitySummary();
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadVersions(), loadActiveModel(), loadQualitySummary()]);
}

async function handleTrain() {
  await runTraining();
}

async function handleActivate(versionId: number) {
  try {
    await activateModelVersion(versionId);
    ElMessage.success('模型版本已激活');
    await Promise.all([loadVersions(), loadActiveModel()]);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  }
}

function handleReuseConfig(version: ModelVersionSummary) {
  applyVersionConfig(version);
  ElMessage.success(`已将 ${version.name} 的训练参数加载到表单`);
}

async function handleRetrain(version: ModelVersionSummary) {
  applyVersionConfig(version, false);
  await runTraining(buildRerunName(version.name));
}

function goToCausalResult(modelVersionId: number) {
  void router.push({
    path: '/causal-results',
    query: {
      modelVersionId: String(modelVersionId),
    },
  });
}

function goToQualityPage() {
  void router.push('/data-quality');
}

function scrollToCompare() {
  document.getElementById('model-compare')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

onMounted(() => {
  void refreshAll();
});
</script>

<style scoped>
.model-hero-aside {
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

.model-hero-aside__eyebrow {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.model-hero-aside h3 {
  margin: 0;
  color: var(--ink-strong);
  font-size: 28px;
  line-height: 1.08;
}

.model-hero-aside p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.block {
  margin-top: 20px;
}

.block__title {
  margin-bottom: 12px;
  color: var(--ink-strong);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.top-gap {
  margin-top: 18px;
}

.training-result-highlight {
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top right, rgba(13, 95, 111, 0.14), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 248, 250, 0.94));
  border: 1px solid rgba(13, 95, 111, 0.12);
}

.training-result-highlight h3 {
  margin: 16px 0 10px;
  color: var(--ink-strong);
  font-size: clamp(28px, 2.3vw, 36px);
  line-height: 1.08;
}

.training-result-highlight p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.compare-selection-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.sticky-bottom-bar__title {
  display: block;
  color: var(--ink-strong);
}

.sticky-bottom-bar__text {
  margin: 6px 0 0;
  color: var(--ink-soft);
}
</style>
