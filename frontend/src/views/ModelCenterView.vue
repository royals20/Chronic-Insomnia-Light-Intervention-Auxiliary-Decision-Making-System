<template>
  <div class="model-center-page">
    <DisclaimerBanner />

    <el-alert
      title="因果获益评估仅用于科研分析演示。因果结论成立依赖可交换性、重叠性、一致性与明确的 X/T/Y 定义，不替代临床诊疗。"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-row :gutter="20">
      <el-col :xs="24" :xl="8">
        <el-card shadow="never" class="panel-card active-card">
          <template #header><span>当前激活模型</span></template>
          <template v-if="activeModel">
            <h3>{{ activeModel.name }}</h3>
            <p>{{ activeModel.description || '暂无说明' }}</p>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="模型类型">{{ activeModel.version_type }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ activeModel.status }}</el-descriptions-item>
              <el-descriptions-item label="估计后端">
                {{ activeModel.engine_backend || '未记录' }}
              </el-descriptions-item>
              <el-descriptions-item label="完成时间">
                {{ formatDateTime(activeModel.training_completed_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="当前没有激活的 causal 模型" />
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="16">
        <el-row :gutter="20">
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="metric-card">
              <span>总样本数</span>
              <strong>{{ overview?.total_patients ?? 0 }}</strong>
              <p>数据库中的受试者总量</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="metric-card">
              <span>可用于因果建模</span>
              <strong>{{ overview?.eligible_records ?? 0 }}</strong>
              <p>同时满足 T、Y 与主要协变量要求的记录</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="metric-card">
              <span>剔除记录数</span>
              <strong>{{ overview?.dropped_records ?? 0 }}</strong>
              <p>主要因为缺少处理变量或结局变量</p>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :xl="13">
        <el-card shadow="never" class="panel-card" v-loading="overviewLoading">
          <template #header><span>数据集概览</span></template>
          <template v-if="overview">
            <el-descriptions :column="2" border class="dataset-desc">
              <el-descriptions-item label="处理变量 T">
                {{ overview.treatment_name }} vs {{ overview.control_name }}
              </el-descriptions-item>
              <el-descriptions-item label="结局变量 Y">
                {{ overview.outcome_name }}
              </el-descriptions-item>
              <el-descriptions-item label="结局均值">
                {{ overview.outcome_summary?.mean_value ?? '未填写' }}
              </el-descriptions-item>
              <el-descriptions-item label="结局范围">
                {{ outcomeRangeText }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="section-block">
              <div class="section-title">当前自动选择特征</div>
              <div class="tag-wrap">
                <el-tag
                  v-for="item in overview.selected_feature_names"
                  :key="item"
                  effect="light"
                  class="tag-item"
                >
                  {{ item }}
                </el-tag>
              </div>
            </div>

            <div class="section-block">
              <div class="section-title">处理组分布</div>
              <el-table :data="overview.treatment_distribution" stripe>
                <el-table-column prop="name" label="分组" min-width="180" />
                <el-table-column prop="value" label="样本数" width="100" />
              </el-table>
            </div>

            <div class="section-block">
              <div class="section-title">字段覆盖率</div>
              <el-table :data="overview.feature_coverage" stripe max-height="320">
                <el-table-column prop="feature_label" label="特征" min-width="140" />
                <el-table-column prop="coverage_rate" label="覆盖率(%)" width="110" />
                <el-table-column prop="missing_count" label="缺失数" width="90" />
                <el-table-column label="已选中" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.selected ? 'success' : 'info'" effect="light">
                      {{ row.selected ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="section-block" v-if="overview.dropped_examples.length > 0">
              <div class="section-title">剔除样例</div>
              <ul class="plain-list">
                <li v-for="item in overview.dropped_examples" :key="item">{{ item }}</li>
              </ul>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="11">
        <el-card shadow="never" class="panel-card">
          <template #header><span>训练任务发起</span></template>
          <el-form label-position="top">
            <el-form-item label="模型名称">
              <el-input v-model="trainForm.model_name" placeholder="为空时自动生成版本名" />
            </el-form-item>
            <el-form-item label="验证集比例">
              <el-input-number v-model="trainForm.test_ratio" :min="0.1" :max="0.4" :step="0.05" class="full-width" />
            </el-form-item>
            <el-form-item label="随机种子">
              <el-input-number v-model="trainForm.random_seed" :min="1" :max="99999999" class="full-width" />
            </el-form-item>
            <el-form-item label="最大特征数">
              <el-input-number v-model="trainForm.max_features" :min="4" :max="16" class="full-width" />
            </el-form-item>
            <el-form-item label="最小特征覆盖率">
              <el-input-number
                v-model="trainForm.min_feature_coverage"
                :min="0.3"
                :max="1"
                :step="0.05"
                class="full-width"
              />
            </el-form-item>
            <el-form-item label="自定义特征名（可选，逗号分隔）">
              <el-input
                v-model="featureNamesText"
                placeholder="例如 age,psqi_score,isi_score,sleep_efficiency"
              />
            </el-form-item>
            <el-form-item label="训练后自动激活">
              <el-switch v-model="trainForm.activate_after_train" />
            </el-form-item>

            <div class="toolbar">
              <el-button type="primary" :loading="trainingLoading" @click="handleTrain">
                发起训练
              </el-button>
              <el-button @click="refreshAll">刷新概览</el-button>
            </div>
          </el-form>

          <el-alert
            title="若本地缺少 econml/sklearn 等真实依赖，系统会自动降级为占位估计器，但接口和版本管理流程保持不变。"
            type="info"
            :closable="false"
            show-icon
            class="top-gap"
          />
        </el-card>

        <el-card shadow="never" class="panel-card" v-if="latestTraining">
          <template #header><span>最新训练结果摘要</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="模型版本">
              {{ latestTraining.model_version.name }}
            </el-descriptions-item>
            <el-descriptions-item label="ATE">
              {{ latestTraining.result.ate }}
            </el-descriptions-item>
            <el-descriptions-item label="验证集 ATE">
              {{ latestTraining.result.validation_ate ?? '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="估计后端">
              {{ latestTraining.result.engine_backend }}
            </el-descriptions-item>
            <el-descriptions-item label="说明">
              {{ latestTraining.result.estimator_message }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="toolbar top-gap">
            <el-button type="primary" plain @click="goToCausalResult(latestTraining.model_version.id)">
              查看结果页
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel-card" v-loading="versionsLoading">
      <template #header><span>模型版本列表</span></template>
      <el-table :data="versions" stripe>
        <el-table-column prop="name" label="版本名称" min-width="180" />
        <el-table-column prop="version_type" label="类型" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="engine_backend" label="估计后端" min-width="160" />
        <el-table-column label="训练完成时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.training_completed_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="220">
          <template #default="{ row }">
            <div class="toolbar">
              <el-button
                text
                type="primary"
                :disabled="row.status === 'active'"
                @click="handleActivate(row.id)"
              >
                设为激活
              </el-button>
              <el-button
                text
                type="primary"
                :disabled="!row.artifact_path"
                @click="goToCausalResult(row.id)"
              >
                查看结果
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import {
  activateModelVersion,
  fetchActiveModel,
  fetchCausalDatasetOverview,
  fetchModelVersions,
  trainCausalModel,
  type CausalTrainingResponse,
  type DatasetOverviewResponse,
  type ModelVersionSummary,
} from '@/api/modelCenter';
import { formatDateTime } from '@/utils/format';

const router = useRouter();
const overview = ref<DatasetOverviewResponse | null>(null);
const activeModel = ref<ModelVersionSummary | null>(null);
const versions = ref<ModelVersionSummary[]>([]);
const latestTraining = ref<CausalTrainingResponse | null>(null);
const overviewLoading = ref(false);
const versionsLoading = ref(false);
const trainingLoading = ref(false);
const featureNamesText = ref('');
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
    return '未填写';
  }
  return `${overview.value.outcome_summary.min_value} ~ ${overview.value.outcome_summary.max_value}`;
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
    versions.value = await fetchModelVersions();
  } finally {
    versionsLoading.value = false;
  }
}

async function loadActiveModel() {
  const data = await fetchActiveModel('causal');
  activeModel.value = data.active_model;
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadVersions(), loadActiveModel()]);
}

async function handleTrain() {
  trainingLoading.value = true;
  try {
    const featureNames = featureNamesText.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    latestTraining.value = await trainCausalModel({
      model_name: trainForm.model_name || undefined,
      test_ratio: trainForm.test_ratio,
      random_seed: trainForm.random_seed,
      max_features: trainForm.max_features,
      min_feature_coverage: trainForm.min_feature_coverage,
      feature_names: featureNames.length > 0 ? featureNames : undefined,
      activate_after_train: trainForm.activate_after_train,
    });
    ElMessage.success(latestTraining.value.message);
    await refreshAll();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    trainingLoading.value = false;
  }
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

function goToCausalResult(modelVersionId: number) {
  void router.push({
    path: '/causal-results',
    query: {
      modelVersionId: String(modelVersionId),
    },
  });
}

onMounted(() => {
  void refreshAll();
});
</script>

<style scoped>
.model-center-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-card,
.metric-card {
  border-radius: 16px;
}

.active-card h3 {
  margin: 0 0 8px;
  color: #173654;
  font-size: 22px;
}

.active-card p {
  margin: 0 0 16px;
  color: #6d8094;
  line-height: 1.7;
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

.dataset-desc,
.top-gap {
  margin-top: 16px;
}

.section-block {
  margin-top: 20px;
}

.section-title {
  margin-bottom: 10px;
  color: #173654;
  font-size: 15px;
  font-weight: 600;
}

.tag-wrap,
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tag-item {
  margin-right: 0;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  color: #4d647a;
  line-height: 1.8;
}

.full-width {
  width: 100%;
}
</style>

