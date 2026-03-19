<template>
  <div class="subject-detail-page" v-loading="loading">
    <DisclaimerBanner />

    <template v-if="patient">
      <SubjectHeaderCard :patient="patient">
        <template #actions>
          <el-button plain @click="goBack">返回列表</el-button>
          <el-button type="primary" plain @click="goToSection('baseline')">基线录入</el-button>
          <el-button type="primary" plain @click="goToSection('questionnaire')">量表录入</el-button>
          <el-button type="primary" plain @click="goToSection('sleep')">睡眠指标</el-button>
          <el-button type="primary" plain @click="goToSection('light')">光干预录入</el-button>
          <el-button type="primary" plain @click="goToSection('followup')">随访录入</el-button>
        </template>
      </SubjectHeaderCard>

      <el-row :gutter="20">
        <el-col :xs="24" :xl="16">
          <div class="left-column">
            <el-card shadow="never" class="section-card">
              <template #header><span>基本信息</span></template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="患者编号">{{ patient.patient_code }}</el-descriptions-item>
                <el-descriptions-item label="匿名编号">{{ patient.anonymized_code }}</el-descriptions-item>
                <el-descriptions-item label="性别">{{ formatValue(patient.gender) }}</el-descriptions-item>
                <el-descriptions-item label="年龄">{{ formatValue(patient.age) }}</el-descriptions-item>
                <el-descriptions-item label="身高(cm)">{{ formatValue(patient.height_cm) }}</el-descriptions-item>
                <el-descriptions-item label="体重(kg)">{{ formatValue(patient.weight_kg) }}</el-descriptions-item>
                <el-descriptions-item label="教育程度">{{ formatValue(patient.education_level) }}</el-descriptions-item>
                <el-descriptions-item label="更新时间">{{ formatDateTime(patient.updated_at) }}</el-descriptions-item>
                <el-descriptions-item label="备注" :span="2">{{ formatValue(patient.remarks) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="section-card">
              <template #header><span>基线概况</span></template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="作息">{{ formatValue(patient.baseline_feature?.work_rest_schedule) }}</el-descriptions-item>
                <el-descriptions-item label="病程">{{ formatValue(patient.baseline_feature?.disease_duration) }}</el-descriptions-item>
                <el-descriptions-item label="用药" :span="2">{{ formatValue(patient.baseline_feature?.medication_usage) }}</el-descriptions-item>
                <el-descriptions-item label="合并症" :span="2">{{ formatValue(patient.baseline_feature?.comorbidities) }}</el-descriptions-item>
                <el-descriptions-item label="心理状态" :span="2">{{ formatValue(patient.baseline_feature?.psychological_status) }}</el-descriptions-item>
                <el-descriptions-item label="睡眠习惯" :span="2">{{ formatValue(patient.baseline_feature?.sleep_habits) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="section-card">
              <template #header><span>量表与客观睡眠指标</span></template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="PSQI">{{ formatValue(patient.questionnaire_score?.psqi_score) }}</el-descriptions-item>
                <el-descriptions-item label="ISI">{{ formatValue(patient.questionnaire_score?.isi_score) }}</el-descriptions-item>
                <el-descriptions-item label="焦虑评分">{{ formatValue(patient.questionnaire_score?.anxiety_score) }}</el-descriptions-item>
                <el-descriptions-item label="抑郁评分">{{ formatValue(patient.questionnaire_score?.depression_score) }}</el-descriptions-item>
                <el-descriptions-item label="评估日期">{{ formatDate(patient.questionnaire_score?.assessed_at) }}</el-descriptions-item>
                <el-descriptions-item label="总睡眠时间(h)">{{ formatValue(patient.sleep_metric?.total_sleep_time_hours) }}</el-descriptions-item>
                <el-descriptions-item label="入睡潜伏期(min)">{{ formatValue(patient.sleep_metric?.sleep_latency_minutes) }}</el-descriptions-item>
                <el-descriptions-item label="睡眠效率(%)">{{ formatValue(patient.sleep_metric?.sleep_efficiency) }}</el-descriptions-item>
                <el-descriptions-item label="觉醒次数">{{ formatValue(patient.sleep_metric?.awakening_count) }}</el-descriptions-item>
                <el-descriptions-item label="睡眠备注" :span="2">{{ formatValue(patient.sleep_metric?.notes) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="section-card">
              <template #header><span>光干预方案</span></template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="光照强度(lux)">{{ formatValue(patient.light_intervention?.intensity_lux) }}</el-descriptions-item>
                <el-descriptions-item label="开始时段">{{ formatValue(patient.light_intervention?.start_period) }}</el-descriptions-item>
                <el-descriptions-item label="持续时间(min)">{{ formatValue(patient.light_intervention?.duration_minutes) }}</el-descriptions-item>
                <el-descriptions-item label="干预天数">{{ formatValue(patient.light_intervention?.intervention_days) }}</el-descriptions-item>
                <el-descriptions-item label="依从性">{{ formatValue(patient.light_intervention?.adherence) }}</el-descriptions-item>
                <el-descriptions-item label="不良反应" :span="2">{{ formatValue(patient.light_intervention?.adverse_events) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="section-card">
              <template #header><span>随访结果</span></template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="随访日期">{{ formatDate(patient.followup_outcome?.followup_date) }}</el-descriptions-item>
                <el-descriptions-item label="主要结局">{{ formatValue(patient.followup_outcome?.primary_outcome) }}</el-descriptions-item>
                <el-descriptions-item label="次要结局" :span="2">{{ formatValue(patient.followup_outcome?.secondary_outcome) }}</el-descriptions-item>
                <el-descriptions-item label="备注" :span="2">{{ formatValue(patient.followup_outcome?.notes) }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </el-col>

        <el-col :xs="24" :xl="8">
          <div class="right-column">
            <el-card shadow="never" class="section-card">
              <template #header><span>完整时间轴</span></template>
              <el-timeline>
                <el-timeline-item
                  v-for="item in timelineItems"
                  :key="`${item.title}-${item.timestamp}`"
                  :timestamp="item.timestamp"
                  placement="top"
                >
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.content }}</p>
                </el-timeline-item>
              </el-timeline>
            </el-card>

            <el-card shadow="never" class="section-card">
              <template #header><span>预测记录占位区</span></template>
              <template v-if="patient.prediction_result">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="推荐等级">{{ formatValue(patient.prediction_result.recommendation_level) }}</el-descriptions-item>
                  <el-descriptions-item label="推荐评分">{{ formatValue(patient.prediction_result.score) }}</el-descriptions-item>
                  <el-descriptions-item label="模型版本">
                    {{ formatValue(patient.prediction_result.model_version?.name) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="生成时间">{{ formatDateTime(patient.prediction_result.generated_at) }}</el-descriptions-item>
                  <el-descriptions-item label="解释文本">{{ formatValue(patient.prediction_result.explanation_text) }}</el-descriptions-item>
                </el-descriptions>
              </template>
              <el-empty v-else description="当前仅展示预测结果占位区，后续可扩展推荐解释与模型对比。" />
            </el-card>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import type { PatientDetail } from '@/api/subjects';
import { fetchPatientDetail } from '@/api/subjects';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import SubjectHeaderCard from '@/components/SubjectHeaderCard.vue';
import { formatDate, formatDateTime, formatValue } from '@/utils/format';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const patient = ref<PatientDetail | null>(null);

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '加载受试者详情失败';
}

const patientId = computed(() => Number(route.params.id));

const timelineItems = computed(() => {
  if (!patient.value) {
    return [];
  }

  const current = patient.value;
  const items = [
    {
      title: '受试者建档',
      timestamp: formatDateTime(current.created_at),
      content: `建档完成，患者编号 ${current.patient_code}`,
      raw: current.created_at,
    },
  ];

  if (current.baseline_feature?.updated_at) {
    items.push({
      title: '基线特征录入',
      timestamp: formatDateTime(current.baseline_feature.updated_at),
      content: '已录入作息、病程、用药和睡眠习惯等基线信息',
      raw: current.baseline_feature.updated_at,
    });
  }

  if (current.questionnaire_score?.assessed_at) {
    items.push({
      title: '量表评估',
      timestamp: formatDate(current.questionnaire_score.assessed_at),
      content: `PSQI ${formatValue(current.questionnaire_score.psqi_score)}，ISI ${formatValue(current.questionnaire_score.isi_score)}`,
      raw: current.questionnaire_score.assessed_at,
    });
  }

  if (current.sleep_metric?.updated_at) {
    items.push({
      title: '客观睡眠指标录入',
      timestamp: formatDateTime(current.sleep_metric.updated_at),
      content: `总睡眠时间 ${formatValue(current.sleep_metric.total_sleep_time_hours)} 小时`,
      raw: current.sleep_metric.updated_at,
    });
  }

  if (current.light_intervention?.updated_at) {
    items.push({
      title: '光干预方案录入',
      timestamp: formatDateTime(current.light_intervention.updated_at),
      content: `光照强度 ${formatValue(current.light_intervention.intensity_lux)} lux，持续 ${formatValue(current.light_intervention.duration_minutes)} 分钟`,
      raw: current.light_intervention.updated_at,
    });
  }

  if (current.followup_outcome?.followup_date) {
    items.push({
      title: '随访结局录入',
      timestamp: formatDate(current.followup_outcome.followup_date),
      content: formatValue(current.followup_outcome.primary_outcome),
      raw: current.followup_outcome.followup_date,
    });
  }

  if (current.prediction_result?.generated_at) {
    items.push({
      title: '预测结果生成',
      timestamp: formatDateTime(current.prediction_result.generated_at),
      content: `推荐等级 ${formatValue(current.prediction_result.recommendation_level)}，用于科研演示`,
      raw: current.prediction_result.generated_at,
    });
  }

  return items.sort((a, b) => String(a.raw).localeCompare(String(b.raw)));
});

async function loadDetail() {
  loading.value = true;
  try {
    patient.value = await fetchPatientDetail(patientId.value);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function goToSection(section: string) {
  void router.push(`/subjects/${patientId.value}/${section}`);
}

function goBack() {
  void router.push('/subjects');
}

onMounted(() => {
  void loadDetail();
});

watch(patientId, () => {
  void loadDetail();
});
</script>

<style scoped>
.subject-detail-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  border-radius: 16px;
}
</style>
