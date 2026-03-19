<template>
  <div class="section-editor-page" v-loading="loading">
    <DisclaimerBanner />

    <template v-if="patient">
      <SubjectHeaderCard :patient="patient">
        <template #actions>
          <el-button plain @click="goToDetail">返回详情</el-button>
          <el-button type="primary" plain @click="goToList">返回列表</el-button>
        </template>
      </SubjectHeaderCard>

      <el-card shadow="never" class="editor-card">
        <template #header>
          <div class="card-header">
            <div>
              <h3>{{ currentConfig.title }}</h3>
              <p>{{ currentConfig.description }}</p>
            </div>
            <el-tag type="warning">仅供科研辅助，不替代临床诊断与治疗</el-tag>
          </div>
        </template>

        <el-form ref="formRef" :model="formModel" :rules="currentRules" label-position="top">
          <el-row :gutter="18">
            <el-col
              v-for="field in currentConfig.fields"
              :key="field.prop"
              :xs="24"
              :md="field.type === 'textarea' ? 24 : 12"
            >
              <el-form-item :label="field.label" :prop="field.prop">
                <el-input
                  v-if="field.type === 'text'"
                  v-model="formModel[field.prop]"
                  :placeholder="field.placeholder"
                />

                <el-input
                  v-else-if="field.type === 'textarea'"
                  v-model="formModel[field.prop]"
                  type="textarea"
                  :rows="4"
                  :placeholder="field.placeholder"
                />

                <el-input-number
                  v-else-if="field.type === 'number'"
                  v-model="formModel[field.prop]"
                  :min="field.min"
                  :max="field.max"
                  :precision="field.precision"
                  controls-position="right"
                  class="full-width"
                />

                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="formModel[field.prop]"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="请选择日期"
                  class="full-width"
                />

                <el-select
                  v-else-if="field.type === 'select'"
                  v-model="formModel[field.prop]"
                  :placeholder="field.placeholder"
                  class="full-width"
                >
                  <el-option
                    v-for="option in field.options || []"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <div class="editor-footer">
            <el-button @click="reloadSection">重置为当前保存内容</el-button>
            <el-button type="primary" :loading="saving" @click="handleSubmit">保存当前页面</el-button>
          </div>
        </el-form>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  type BaselineFeature,
  fetchPatientDetail,
  type FollowupOutcome,
  type LightIntervention,
  type QuestionnaireScore,
  saveBaselineFeature,
  saveFollowupOutcome,
  saveLightIntervention,
  saveQuestionnaireScore,
  saveSleepMetric,
  type SleepMetric,
  type PatientDetail,
} from '@/api/subjects';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import SubjectHeaderCard from '@/components/SubjectHeaderCard.vue';

type SectionKey = 'baseline' | 'questionnaire' | 'sleep' | 'light' | 'followup';
type FieldType = 'text' | 'textarea' | 'number' | 'date' | 'select';
type FormValue = string | number | null;
type FormModel = Record<string, FormValue>;

interface FieldConfig {
  prop: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  min?: number;
  max?: number;
  precision?: number;
  options?: Array<{ label: string; value: string }>;
}

interface SectionConfig {
  title: string;
  description: string;
  fields: FieldConfig[];
}

const route = useRoute();
const router = useRouter();
const patient = ref<PatientDetail | null>(null);
const loading = ref(false);
const saving = ref(false);
const formRef = ref<FormInstance>();

const allKeys = [
  'work_rest_schedule',
  'disease_duration',
  'medication_usage',
  'comorbidities',
  'psychological_status',
  'sleep_habits',
  'notes',
  'psqi_score',
  'isi_score',
  'anxiety_score',
  'depression_score',
  'assessed_at',
  'total_sleep_time_hours',
  'sleep_latency_minutes',
  'sleep_efficiency',
  'awakening_count',
  'intensity_lux',
  'start_period',
  'duration_minutes',
  'intervention_days',
  'adherence',
  'adverse_events',
  'followup_date',
  'primary_outcome',
  'secondary_outcome',
] as const;

const formModel = reactive<FormModel>(
  allKeys.reduce((acc, key) => {
    acc[key] = null;
    return acc;
  }, {} as FormModel),
);

const sectionConfigs: Record<SectionKey, SectionConfig> = {
  baseline: {
    title: '基线特征录入页',
    description: '录入作息、病程、用药、合并症、心理状态和睡眠习惯等信息。',
    fields: [
      { prop: 'work_rest_schedule', label: '作息', type: 'text', placeholder: '例如 23:00-07:00' },
      { prop: 'disease_duration', label: '病程', type: 'text', placeholder: '例如 18个月' },
      { prop: 'medication_usage', label: '用药', type: 'textarea', placeholder: '请输入当前或既往用药情况' },
      { prop: 'comorbidities', label: '合并症', type: 'textarea', placeholder: '请输入合并症信息' },
      { prop: 'psychological_status', label: '心理状态', type: 'textarea', placeholder: '请输入心理状态描述' },
      { prop: 'sleep_habits', label: '睡眠习惯', type: 'textarea', placeholder: '请输入睡前行为、午睡情况等' },
      { prop: 'notes', label: '备注', type: 'textarea', placeholder: '其他补充说明' },
    ],
  },
  questionnaire: {
    title: '量表录入页',
    description: '录入 PSQI、ISI 以及焦虑/抑郁相关分数。',
    fields: [
      { prop: 'psqi_score', label: 'PSQI', type: 'number', min: 0, max: 30, precision: 1 },
      { prop: 'isi_score', label: 'ISI', type: 'number', min: 0, max: 30, precision: 1 },
      { prop: 'anxiety_score', label: '焦虑评分', type: 'number', min: 0, max: 30, precision: 1 },
      { prop: 'depression_score', label: '抑郁评分', type: 'number', min: 0, max: 30, precision: 1 },
      { prop: 'assessed_at', label: '评估日期', type: 'date' },
    ],
  },
  sleep: {
    title: '客观睡眠指标录入页',
    description: '录入总睡眠时间、入睡潜伏期、睡眠效率和觉醒次数。',
    fields: [
      { prop: 'total_sleep_time_hours', label: '总睡眠时间(h)', type: 'number', min: 0, max: 24, precision: 1 },
      { prop: 'sleep_latency_minutes', label: '入睡潜伏期(min)', type: 'number', min: 0, max: 300, precision: 1 },
      { prop: 'sleep_efficiency', label: '睡眠效率(%)', type: 'number', min: 0, max: 100, precision: 1 },
      { prop: 'awakening_count', label: '觉醒次数', type: 'number', min: 0, max: 20, precision: 0 },
      { prop: 'notes', label: '备注', type: 'textarea', placeholder: '记录设备来源或分析说明' },
    ],
  },
  light: {
    title: '光干预记录页',
    description: '记录光照强度、开始时段、持续时间、天数、依从性和不良反应。',
    fields: [
      { prop: 'intensity_lux', label: '光照强度(lux)', type: 'number', min: 0, max: 20000, precision: 1 },
      { prop: 'start_period', label: '开始时段', type: 'text', placeholder: '例如 07:30' },
      { prop: 'duration_minutes', label: '持续时间(min)', type: 'number', min: 0, max: 240, precision: 0 },
      { prop: 'intervention_days', label: '干预天数', type: 'number', min: 0, max: 180, precision: 0 },
      {
        prop: 'adherence',
        label: '依从性',
        type: 'select',
        placeholder: '请选择依从性',
        options: [
          { label: '高', value: '高' },
          { label: '中', value: '中' },
          { label: '低', value: '低' },
        ],
      },
      { prop: 'adverse_events', label: '不良反应', type: 'textarea', placeholder: '请输入观察到的不良反应' },
    ],
  },
  followup: {
    title: '随访结局录入页',
    description: '记录随访日期、主要结局、次要结局和备注。',
    fields: [
      { prop: 'followup_date', label: '随访日期', type: 'date' },
      { prop: 'primary_outcome', label: '主要结局', type: 'textarea', placeholder: '请输入主要结局变化' },
      { prop: 'secondary_outcome', label: '次要结局', type: 'textarea', placeholder: '请输入次要结局变化' },
      { prop: 'notes', label: '备注', type: 'textarea', placeholder: '补充说明' },
    ],
  },
};

const rulesMap: Record<SectionKey, FormRules<FormModel>> = {
  baseline: {
    work_rest_schedule: [{ required: true, message: '请输入作息信息', trigger: 'blur' }],
    disease_duration: [{ required: true, message: '请输入病程', trigger: 'blur' }],
  },
  questionnaire: {
    assessed_at: [{ required: true, message: '请选择评估日期', trigger: 'change' }],
    psqi_score: [{ required: true, message: '请输入 PSQI', trigger: 'change' }],
  },
  sleep: {
    total_sleep_time_hours: [{ required: true, message: '请输入总睡眠时间', trigger: 'change' }],
    sleep_efficiency: [{ required: true, message: '请输入睡眠效率', trigger: 'change' }],
  },
  light: {
    intensity_lux: [{ required: true, message: '请输入光照强度', trigger: 'change' }],
    start_period: [{ required: true, message: '请输入开始时段', trigger: 'blur' }],
  },
  followup: {
    followup_date: [{ required: true, message: '请选择随访日期', trigger: 'change' }],
    primary_outcome: [{ required: true, message: '请输入主要结局', trigger: 'blur' }],
  },
};

const patientId = computed(() => Number(route.params.id));
const sectionKey = computed(() => route.meta.sectionKey as SectionKey);
const currentConfig = computed(() => sectionConfigs[sectionKey.value]);
const currentRules = computed(() => rulesMap[sectionKey.value]);

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '保存失败，请稍后重试';
}

function clearForm() {
  allKeys.forEach((key) => {
    formModel[key] = null;
  });
}

function applySectionData(currentPatient: PatientDetail) {
  clearForm();

  if (sectionKey.value === 'baseline') {
    Object.assign(formModel, currentPatient.baseline_feature || {});
    return;
  }
  if (sectionKey.value === 'questionnaire') {
    Object.assign(formModel, currentPatient.questionnaire_score || {});
    return;
  }
  if (sectionKey.value === 'sleep') {
    Object.assign(formModel, currentPatient.sleep_metric || {});
    return;
  }
  if (sectionKey.value === 'light') {
    Object.assign(formModel, currentPatient.light_intervention || {});
    return;
  }
  Object.assign(formModel, currentPatient.followup_outcome || {});
}

function buildBaselinePayload(): BaselineFeature {
  return {
    work_rest_schedule: (formModel.work_rest_schedule as string | null) || null,
    disease_duration: (formModel.disease_duration as string | null) || null,
    medication_usage: (formModel.medication_usage as string | null) || null,
    comorbidities: (formModel.comorbidities as string | null) || null,
    psychological_status: (formModel.psychological_status as string | null) || null,
    sleep_habits: (formModel.sleep_habits as string | null) || null,
    notes: (formModel.notes as string | null) || null,
  };
}

function buildQuestionnairePayload(): QuestionnaireScore {
  return {
    psqi_score: (formModel.psqi_score as number | null) ?? null,
    isi_score: (formModel.isi_score as number | null) ?? null,
    anxiety_score: (formModel.anxiety_score as number | null) ?? null,
    depression_score: (formModel.depression_score as number | null) ?? null,
    assessed_at: (formModel.assessed_at as string | null) || null,
  };
}

function buildSleepPayload(): SleepMetric {
  return {
    total_sleep_time_hours: (formModel.total_sleep_time_hours as number | null) ?? null,
    sleep_latency_minutes: (formModel.sleep_latency_minutes as number | null) ?? null,
    sleep_efficiency: (formModel.sleep_efficiency as number | null) ?? null,
    awakening_count: (formModel.awakening_count as number | null) ?? null,
    notes: (formModel.notes as string | null) || null,
  };
}

function buildLightPayload(): LightIntervention {
  return {
    intensity_lux: (formModel.intensity_lux as number | null) ?? null,
    start_period: (formModel.start_period as string | null) || null,
    duration_minutes: (formModel.duration_minutes as number | null) ?? null,
    intervention_days: (formModel.intervention_days as number | null) ?? null,
    adherence: (formModel.adherence as string | null) || null,
    adverse_events: (formModel.adverse_events as string | null) || null,
  };
}

function buildFollowupPayload(): FollowupOutcome {
  return {
    followup_date: (formModel.followup_date as string | null) || null,
    primary_outcome: (formModel.primary_outcome as string | null) || null,
    secondary_outcome: (formModel.secondary_outcome as string | null) || null,
    notes: (formModel.notes as string | null) || null,
  };
}

async function loadPatient() {
  loading.value = true;
  try {
    patient.value = await fetchPatientDetail(patientId.value);
    applySectionData(patient.value);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function reloadSection() {
  await loadPatient();
}

async function handleSubmit() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  saving.value = true;
  try {
    if (sectionKey.value === 'baseline') {
      patient.value = await saveBaselineFeature(patientId.value, buildBaselinePayload());
    } else if (sectionKey.value === 'questionnaire') {
      patient.value = await saveQuestionnaireScore(patientId.value, buildQuestionnairePayload());
    } else if (sectionKey.value === 'sleep') {
      patient.value = await saveSleepMetric(patientId.value, buildSleepPayload());
    } else if (sectionKey.value === 'light') {
      patient.value = await saveLightIntervention(patientId.value, buildLightPayload());
    } else {
      patient.value = await saveFollowupOutcome(patientId.value, buildFollowupPayload());
    }
    if (patient.value) {
      applySectionData(patient.value);
    }
    ElMessage.success('保存成功');
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    saving.value = false;
  }
}

function goToDetail() {
  void router.push(`/subjects/${patientId.value}`);
}

function goToList() {
  void router.push('/subjects');
}

onMounted(() => {
  void loadPatient();
});

watch([patientId, sectionKey], () => {
  void loadPatient();
});
</script>

<style scoped>
.section-editor-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-card {
  border-radius: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.card-header h3 {
  margin: 0 0 8px;
  color: #173654;
}

.card-header p {
  margin: 0;
  color: #74869a;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.full-width {
  width: 100%;
}

@media (max-width: 960px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
