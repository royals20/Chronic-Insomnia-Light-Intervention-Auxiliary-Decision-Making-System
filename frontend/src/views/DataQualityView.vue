<template>
  <div class="quality-page" v-loading="loading">
    <DisclaimerBanner />

    <template v-if="quality">
      <el-alert
        :title="`当前共有 ${quality.summary.affected_patient_count} 例受试者存在需补录或复核的问题，可直接联动到数据中心处理。`"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="alert-actions">
            <span>优先处理阻塞问题，再发起推荐评估和因果训练。</span>
            <el-button type="primary" plain size="small" @click="goToDataCenter">
              去数据中心补录
            </el-button>
          </div>
        </template>
      </el-alert>

      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>受试者总数</span>
            <strong>{{ quality.summary.total_patients }}</strong>
            <p>当前数据库中的受试者总量</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>完整资料数</span>
            <strong>{{ quality.summary.complete_patients }}</strong>
            <p>基础字段与核心表单都已录入</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>可建模样本</span>
            <strong>{{ quality.summary.modeling_ready_patients }}</strong>
            <p>满足当前 T/Y 解析条件的样本数</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>阻塞问题数</span>
            <strong>{{ quality.summary.blocking_issue_count }}</strong>
            <p>会直接影响推荐或因果训练</p>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :xl="4.8">
          <el-card shadow="never" class="metric-card">
            <span>平均完成率</span>
            <strong>{{ quality.summary.average_completion_rate }}%</strong>
            <p>按核心字段统计的平均录入率</p>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>缺失值统计</span></template>
            <el-table :data="quality.summary.missing_fields" stripe>
              <el-table-column prop="field_label" label="字段" min-width="120" />
              <el-table-column prop="missing_count" label="缺失数" width="90" />
              <el-table-column prop="missing_rate" label="缺失率(%)" width="110" />
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>字段完成率</span></template>
            <el-table :data="quality.summary.completion_stats" stripe>
              <el-table-column prop="field_label" label="字段" min-width="120" />
              <el-table-column prop="completed_count" label="已完成" width="90" />
              <el-table-column prop="completion_rate" label="完成率(%)" width="110" />
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="8">
          <el-card shadow="never" class="panel-card">
            <template #header><span>建议补录动作</span></template>
            <el-table :data="quality.suggested_fixes" stripe max-height="360">
              <el-table-column prop="title" label="动作" min-width="160" />
              <el-table-column prop="patient_count" label="受影响人数" width="110" />
              <el-table-column prop="description" label="说明" min-width="220" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>阻塞问题</span></template>
            <el-table :data="quality.blocking_issues" stripe max-height="420">
              <el-table-column prop="patient_code" label="患者编号" min-width="110">
                <template #default="{ row }">
                  {{ row.patient_code || '全局' }}
                </template>
              </el-table-column>
              <el-table-column prop="issue_type" label="问题类型" min-width="150" />
              <el-table-column prop="message" label="问题说明" min-width="240" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button
                    v-if="row.patient_id"
                    text
                    type="primary"
                    @click="goToSubject(row.patient_id)"
                  >
                    查看受试者
                  </el-button>
                  <span v-else class="muted-text">全局问题</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="12">
          <el-card shadow="never" class="panel-card">
            <template #header><span>预警问题</span></template>
            <el-table :data="quality.warning_issues" stripe max-height="420">
              <el-table-column prop="patient_code" label="患者编号" min-width="110">
                <template #default="{ row }">
                  {{ row.patient_code || '全局' }}
                </template>
              </el-table-column>
              <el-table-column prop="issue_type" label="问题类型" min-width="150" />
              <el-table-column prop="suggested_action" label="建议动作" min-width="240" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button
                    v-if="row.patient_id"
                    text
                    type="primary"
                    @click="goToSubject(row.patient_id)"
                  >
                    查看受试者
                  </el-button>
                  <span v-else class="muted-text">全局问题</span>
                </template>
              </el-table-column>
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

    <el-empty v-else description="暂无数据质量结果" />
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import type { DataQualityResponse } from '@/api/subjects';
import { fetchQualitySummary } from '@/api/subjects';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';

const router = useRouter();
const loading = ref(false);
const quality = ref<DataQualityResponse | null>(null);
const genderChartRef = ref<HTMLElement | null>(null);
const completionChartRef = ref<HTMLElement | null>(null);
const ageChartRef = ref<HTMLElement | null>(null);
let genderChart: echarts.ECharts | null = null;
let completionChart: echarts.ECharts | null = null;
let ageChart: echarts.ECharts | null = null;

function renderCharts() {
  if (!quality.value || !genderChartRef.value || !completionChartRef.value || !ageChartRef.value) {
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
        data: quality.value.summary.gender_distribution,
      },
    ],
  });

  completionChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: quality.value.summary.section_completion.map((item) => item.name),
      axisLabel: { interval: 0, rotate: 18 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'bar',
        data: quality.value.summary.section_completion.map((item) => item.value),
        itemStyle: { color: '#1677c8', borderRadius: [6, 6, 0, 0] },
      },
    ],
  });

  ageChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: quality.value.summary.age_bucket_distribution.map((item) => item.name),
      axisLabel: { interval: 0 },
    },
    yAxis: { type: 'value', name: '人数' },
    series: [
      {
        type: 'line',
        smooth: true,
        data: quality.value.summary.age_bucket_distribution.map((item) => item.value),
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
    quality.value = await fetchQualitySummary();
    await nextTick();
    renderCharts();
  } finally {
    loading.value = false;
  }
}

function goToDataCenter() {
  void router.push({
    path: '/data-center',
    query: {
      quality: 'attention',
    },
  });
}

function goToSubject(patientId: number) {
  void router.push(`/subjects/${patientId}`);
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

.alert-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
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

.muted-text {
  color: #728397;
  font-size: 13px;
}

@media (max-width: 960px) {
  .alert-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
