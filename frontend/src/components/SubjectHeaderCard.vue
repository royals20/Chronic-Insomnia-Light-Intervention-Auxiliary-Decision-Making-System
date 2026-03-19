<template>
  <el-card shadow="never" class="subject-card">
    <div class="subject-card__main">
      <div>
        <div class="subject-card__badge">受试者档案</div>
        <h3>{{ patient.patient_code }}</h3>
        <p>
          匿名编号：{{ patient.anonymized_code }} ｜ 性别：{{ formatValue(patient.gender) }} ｜ 年龄：{{ formatValue(patient.age) }}
        </p>
      </div>
      <div class="subject-card__actions">
        <slot name="actions" />
      </div>
    </div>

    <el-row :gutter="16" class="subject-card__stats">
      <el-col :xs="12" :md="6">
        <div class="mini-stat">
          <span>基线特征</span>
          <strong>{{ patient.has_baseline_feature ? '已录入' : '待录入' }}</strong>
        </div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="mini-stat">
          <span>量表评分</span>
          <strong>{{ patient.has_questionnaire_score ? '已录入' : '待录入' }}</strong>
        </div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="mini-stat">
          <span>光干预</span>
          <strong>{{ patient.has_light_intervention ? '已录入' : '待录入' }}</strong>
        </div>
      </el-col>
      <el-col :xs="12" :md="6">
        <div class="mini-stat">
          <span>随访结局</span>
          <strong>{{ patient.has_followup_outcome ? '已录入' : '待录入' }}</strong>
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import type { PatientDetail, PatientListItem } from '@/api/subjects';
import { formatValue } from '@/utils/format';

defineProps<{
  patient: PatientDetail | PatientListItem;
}>();
</script>

<style scoped>
.subject-card {
  border-radius: 18px;
  background: linear-gradient(135deg, #f9fcff 0%, #f2f7fc 100%);
}

.subject-card__main {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.subject-card__badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(18, 60, 101, 0.12);
  color: #123c65;
  font-size: 12px;
  margin-bottom: 12px;
}

.subject-card h3 {
  margin: 0 0 10px;
  color: #143b63;
  font-size: 26px;
}

.subject-card p {
  margin: 0;
  color: #607487;
  line-height: 1.8;
}

.subject-card__actions {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.subject-card__stats {
  margin-top: 20px;
}

.mini-stat {
  padding: 14px 16px;
  border-radius: 14px;
  background: #fff;
  min-height: 88px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mini-stat span {
  font-size: 13px;
  color: #6f8294;
}

.mini-stat strong {
  font-size: 20px;
  color: #173654;
}

@media (max-width: 960px) {
  .subject-card__main {
    flex-direction: column;
  }

  .subject-card__actions {
    flex-wrap: wrap;
  }
}
</style>
