<template>
  <div class="quality-page" v-loading="loading">
    <DisclaimerBanner />

    <template v-if="summary">
      <el-row :gutter="20">
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="metric-card">
            <span>受试者总数</span>
            <strong>{{ summary.total_patients }}</strong>
            <p>当前数据库中的受试者总量</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="metric-card">
            <span>异常提示数</span>
            <strong>{{ summary.anomalies.length }}</strong>
            <p>建议人工复核的记录数量</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="metric-card">
            <span>平均字段完成率</span>
            <strong>{{ averageCompletionRate }}%</strong>
            <p>按核心字段统计的平均完成情况</p>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>缺失值统计</span></template>
            <el-table :data="summary.missing_fields" stripe>
              <el-table-column prop="field_label" label="字段" min-width="120" />
              <el-table-column prop="missing_count" label="缺失数" width="90" />
              <el-table-column prop="missing_rate" label="缺失率(%)" width="110" />
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>字段完成率</span></template>
            <el-table :data="summary.completion_stats" stripe>
              <el-table-column prop="field_label" label="字段" min-width="120" />
              <el-table-column prop="completed_count" label="已完成" width="90" />
              <el-table-column prop="completion_rate" label="完成率(%)" width="110" />
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>异常值提示</span></template>
            <el-table :data="summary.anomalies" stripe max-height="360">
              <el-table-column prop="patient_code" label="患者编号" min-width="110" />
              <el-table-column prop="issue_type" label="异常类型" min-width="120" />
              <el-table-column prop="message" label="提示信息" min-width="220" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>性别分布</span></template>
            <div ref="genderChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>关键模块完成情况</span></template>
            <div ref="completionChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>年龄分布</span></template>
            <div ref="ageChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import type { DataQualitySummary } from '@/api/subjects';
import { fetchQualitySummary } from '@/api/subjects';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';

const loading = ref(false);
const summary = ref<DataQualitySummary | null>(null);
const genderChartRef = ref<HTMLElement | null>(null);
const completionChartRef = ref<HTMLElement | null>(null);
const ageChartRef = ref<HTMLElement | null>(null);
let genderChart: echarts.ECharts | null = null;
let completionChart: echarts.ECharts | null = null;
let ageChart: echarts.ECharts | null = null;

const averageCompletionRate = computed(() => {
  if (!summary.value || summary.value.completion_stats.length === 0) {
    return 0;
  }
  const total = summary.value.completion_stats.reduce((sum, item) => sum + item.completion_rate, 0);
  return (total / summary.value.completion_stats.length).toFixed(1);
});

function renderCharts() {
  if (!summary.value || !genderChartRef.value || !completionChartRef.value || !ageChartRef.value) {
    return;
  }

  genderChart ??= echarts.init(genderChartRef.value);
  completionChart ??= echarts.init(completionChartRef.value);
  ageChart ??= echarts.init(ageChartRef.value);

  genderChart.setOption({
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '72%'],
        data: summary.value.gender_distribution,
      },
    ],
  });

  completionChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: summary.value.section_completion.map((item) => item.name),
      axisLabel: { interval: 0, rotate: 18 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'bar',
        data: summary.value.section_completion.map((item) => item.value),
        itemStyle: { color: '#1677c8', borderRadius: [6, 6, 0, 0] },
      },
    ],
  });

  ageChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: summary.value.age_bucket_distribution.map((item) => item.name),
      axisLabel: { interval: 0 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'line',
        smooth: true,
        data: summary.value.age_bucket_distribution.map((item) => item.value),
        lineStyle: { color: '#0f8a6b', width: 3 },
        itemStyle: { color: '#0f8a6b' },
        areaStyle: { color: 'rgba(15, 138, 107, 0.15)' },
      },
    ],
  });
}

function resizeCharts() {
  genderChart?.resize();
  completionChart?.resize();
  ageChart?.resize();
}

async function loadSummary() {
  loading.value = true;
  try {
    summary.value = await fetchQualitySummary();
    await nextTick();
    renderCharts();
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadSummary();
  window.addEventListener('resize', resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts);
  genderChart?.dispose();
  completionChart?.dispose();
  ageChart?.dispose();
});
</script>

<style scoped>
.quality-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metric-card,
.panel-card {
  border-radius: 16px;
}

.metric-card span {
  color: #6f8294;
  font-size: 14px;
}

.metric-card strong {
  display: block;
  margin: 14px 0 8px;
  color: #16324f;
  font-size: 34px;
}

.metric-card p {
  margin: 0;
  color: #728397;
  line-height: 1.7;
}

.chart-box {
  height: 320px;
}
</style>
