<template>
  <div class="causal-results-page" v-loading="loading">
    <DisclaimerBanner />

    <el-alert
      title="因果评估结果仅在 X（基线协变量）、T（处理变量）与 Y（结局变量）定义清晰且满足因果前提时才有解释价值。仅供科研分析，不替代临床诊疗。"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-card shadow="never" class="panel-card">
      <div class="toolbar">
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
        <el-button @click="goToModelCenter">返回模型中心</el-button>
      </div>
    </el-card>

    <template v-if="result">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>ATE</span>
            <strong>{{ result.ate }}</strong>
            <p>整体平均处理效应</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>验证集 ATE</span>
            <strong>{{ result.validation_ate ?? '未填写' }}</strong>
            <p>验证集上的平均效应估计</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>观察组间差值</span>
            <strong>{{ result.observed_group_difference ?? '未填写' }}</strong>
            <p>未调整混杂时的处理组差值</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>样本数</span>
            <strong>{{ result.dataset_record_count }}</strong>
            <p>参与本次因果分析的有效记录</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>估计后端</span>
            <strong class="small-text">{{ result.engine_backend }}</strong>
            <p>当前运行的因果估计实现</p>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="panel-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型版本">
            {{ result.model_version.name }}
          </el-descriptions-item>
          <el-descriptions-item label="结果说明">
            {{ result.estimator_message }}
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
          <el-descriptions-item label="选中特征">
            <div class="tag-wrap">
              <el-tag v-for="item in result.selected_feature_names" :key="item" effect="light">
                {{ item }}
              </el-tag>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>个体获益分布</span></template>
            <div ref="distributionChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>特征重要性</span></template>
            <div ref="importanceChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>分层结果</span></template>
            <div ref="subgroupChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>适用前提说明</span></template>
            <ul class="plain-list">
              <li v-for="item in result.assumptions" :key="item">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>限制说明</span></template>
            <ul class="plain-list">
              <li v-for="item in result.limitations" :key="item">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>潜在高获益个体</span></template>
            <el-table :data="result.top_positive_patients" stripe>
              <el-table-column prop="patient_code" label="患者编号" min-width="120" />
              <el-table-column prop="treatment_label" label="当前处理组" min-width="140" />
              <el-table-column prop="observed_outcome" label="观察结局" width="100" />
              <el-table-column prop="estimated_ite" label="估计 ITE" width="100" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>潜在低获益个体</span></template>
            <el-table :data="result.top_negative_patients" stripe>
              <el-table-column prop="patient_code" label="患者编号" min-width="120" />
              <el-table-column prop="treatment_label" label="当前处理组" min-width="140" />
              <el-table-column prop="observed_outcome" label="观察结局" width="100" />
              <el-table-column prop="estimated_ite" label="估计 ITE" width="100" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="请选择模型版本并加载演示级因果评估结果" />
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import {
  fetchCausalResults,
  fetchModelVersions,
  type CausalEvaluationResultResponse,
  type ModelVersionSummary,
} from '@/api/modelCenter';

const route = useRoute();
const router = useRouter();
const causalVersions = ref<ModelVersionSummary[]>([]);
const selectedModelVersionId = ref<number | undefined>();
const result = ref<CausalEvaluationResultResponse | null>(null);
const loading = ref(false);
const distributionChartRef = ref<HTMLElement | null>(null);
const importanceChartRef = ref<HTMLElement | null>(null);
const subgroupChartRef = ref<HTMLElement | null>(null);
let distributionChart: echarts.ECharts | null = null;
let importanceChart: echarts.ECharts | null = null;
let subgroupChart: echarts.ECharts | null = null;

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
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
    grid: { left: 40, right: 20, top: 30, bottom: 50 },
    xAxis: {
      type: 'category',
      data: result.value.ite_distribution.map((item) => item.name),
      axisLabel: { interval: 0, rotate: 18 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'bar',
        data: result.value.ite_distribution.map((item) => item.value),
        itemStyle: { color: '#1677c8', borderRadius: [6, 6, 0, 0] },
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
        itemStyle: { color: '#0f8a6b', borderRadius: [0, 6, 6, 0] },
      },
    ],
  });

  subgroupChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 70 },
    xAxis: {
      type: 'category',
      data: result.value.subgroup_results.map((item) => `${item.feature_label}-${item.subgroup_name}`),
      axisLabel: { interval: 0, rotate: 28 },
    },
    yAxis: { type: 'value', name: '平均 ITE' },
    series: [
      {
        type: 'bar',
        data: result.value.subgroup_results.map((item) => item.average_ite),
        itemStyle: { color: '#d97706', borderRadius: [6, 6, 0, 0] },
      },
    ],
  });
}

function resizeCharts() {
  distributionChart?.resize();
  importanceChart?.resize();
  subgroupChart?.resize();
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
    await nextTick();
    renderCharts();
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
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts);
  distributionChart?.dispose();
  importanceChart?.dispose();
  subgroupChart?.dispose();
});
</script>

<style scoped>
.causal-results-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-card,
.metric-card {
  border-radius: 16px;
}

.toolbar,
.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.model-select {
  width: 360px;
}

.metric-card span {
  color: #6f8294;
  font-size: 14px;
}

.metric-card strong {
  display: block;
  margin: 14px 0 8px;
  color: #16324f;
  font-size: 30px;
}

.metric-card .small-text {
  font-size: 18px;
  line-height: 1.6;
}

.metric-card p {
  margin: 0;
  color: #728397;
  line-height: 1.7;
}

.chart-box {
  height: 320px;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  color: #4d647a;
  line-height: 1.9;
}

@media (max-width: 960px) {
  .model-select {
    width: 100%;
  }
}
</style>
