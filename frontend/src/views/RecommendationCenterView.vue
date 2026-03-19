<template>
  <div class="recommendation-page">
    <DisclaimerBanner />

    <el-tabs v-model="activeTab" class="page-tabs">
      <el-tab-pane label="单例评估" name="single">
        <el-row :gutter="20">
          <el-col :xs="24" :xl="10">
            <el-card shadow="never" class="panel-card">
              <template #header><span>选择受试者</span></template>
              <el-form label-position="top">
                <el-form-item label="受试者">
                  <el-select
                    v-model="selectedPatientId"
                    filterable
                    clearable
                    placeholder="请选择受试者"
                    class="full-width"
                  >
                    <el-option
                      v-for="item in patientOptions"
                      :key="item.id"
                      :label="`${item.patient_code} / ${item.anonymized_code}`"
                      :value="item.id"
                    />
                  </el-select>
                </el-form-item>

                <div class="button-row">
                  <el-button type="primary" :disabled="!selectedPatientId" :loading="singleLoading" @click="runSingle(true)">
                    生成并保存推荐
                  </el-button>
                  <el-button :disabled="!selectedPatientId" :loading="singleLoading" @click="runSingle(false)">
                    仅预览
                  </el-button>
                </div>
              </el-form>

              <el-alert
                title="V1 采用规则/评分版推荐引擎，结果仅供科研辅助，不替代临床诊断与治疗。"
                type="warning"
                :closable="false"
                show-icon
                class="panel-alert"
              />
            </el-card>
          </el-col>

          <el-col :xs="24" :xl="14">
            <el-card shadow="never" class="panel-card">
              <template #header><span>评估结果</span></template>
              <template v-if="singleResult">
                <el-row :gutter="16">
                  <el-col :xs="24" :md="8">
                    <div class="metric-box">
                      <span>数据完整性</span>
                      <strong>{{ singleResult.data_completeness_score }}</strong>
                    </div>
                  </el-col>
                  <el-col :xs="24" :md="8">
                    <div class="metric-box">
                      <span>获益评分</span>
                      <strong>{{ singleResult.benefit_score }}</strong>
                    </div>
                  </el-col>
                  <el-col :xs="24" :md="8">
                    <div class="metric-box">
                      <span>推荐等级</span>
                      <strong class="small-text">{{ singleResult.recommendation_level }}</strong>
                    </div>
                  </el-col>
                </el-row>

                <el-descriptions :column="1" border class="result-desc">
                  <el-descriptions-item label="说明摘要">{{ singleResult.explanation_text }}</el-descriptions-item>
                  <el-descriptions-item label="关键影响因素">
                    <div class="tag-wrap">
                      <el-tag v-for="item in singleResult.key_factors" :key="item" effect="light" class="factor-tag">
                        {{ item }}
                      </el-tag>
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item label="使用限制">
                    <ul class="plain-list">
                      <li v-for="item in singleResult.usage_limitations" :key="item">{{ item }}</li>
                    </ul>
                  </el-descriptions-item>
                  <el-descriptions-item label="引擎版本">
                    {{ singleResult.engine_name }} / {{ singleResult.engine_version }}
                  </el-descriptions-item>
                </el-descriptions>

                <div class="button-row top-gap">
                  <el-button type="primary" plain @click="goToReport(singleResult.patient_id)">查看报告</el-button>
                  <el-button plain @click="goToSubject(singleResult.patient_id)">查看受试者详情</el-button>
                </div>
              </template>
              <el-empty v-else description="请选择受试者并执行评估" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="批量评估" name="batch">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="header-row">
              <span>批量评估列表</span>
              <div class="button-row">
                <el-button type="primary" :disabled="selectedBatchIds.length === 0" :loading="batchLoading" @click="runBatch">
                  批量生成并保存
                </el-button>
              </div>
            </div>
          </template>

          <el-input
            v-model="batchKeyword"
            placeholder="按患者编号或匿名编号过滤"
            clearable
            class="batch-search"
          />

          <el-table :data="filteredBatchPatients" stripe @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="52" />
            <el-table-column prop="patient_code" label="患者编号" min-width="120" />
            <el-table-column prop="anonymized_code" label="匿名编号" min-width="120" />
            <el-table-column prop="gender" label="性别" width="80" />
            <el-table-column prop="age" label="年龄" width="80" />
            <el-table-column label="量表/睡眠资料" min-width="140">
              <template #default="{ row }">
                {{ row.has_questionnaire_score && row.has_sleep_metric ? '较完整' : '待补充' }}
              </template>
            </el-table-column>
          </el-table>

          <template v-if="batchResult" #footer>
            <el-alert
              :title="`批量评估完成：成功 ${batchResult.success_count} 例，失败 ${batchResult.failed_count} 例`"
              :type="batchResult.failed_count > 0 ? 'warning' : 'success'"
              :closable="false"
              show-icon
            />
          </template>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="历史结果查询" name="history">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="header-row">
              <span>历史推荐结果</span>
              <div class="button-row">
                <el-input
                  v-model="historyKeyword"
                  placeholder="按患者编号或匿名编号搜索"
                  clearable
                  class="history-search"
                  @keyup.enter="loadHistory"
                  @clear="loadHistory"
                />
                <el-select v-model="historyLevel" clearable placeholder="推荐等级" class="history-level">
                  <el-option label="推荐光干预" value="推荐光干预" />
                  <el-option label="谨慎推荐并短期复评" value="谨慎推荐并短期复评" />
                  <el-option label="暂不直接推荐" value="暂不直接推荐" />
                </el-select>
                <el-button type="primary" plain @click="loadHistory">查询</el-button>
              </div>
            </div>
          </template>

          <el-table :data="history.items" stripe>
            <el-table-column prop="patient_code" label="患者编号" min-width="120" />
            <el-table-column prop="anonymized_code" label="匿名编号" min-width="120" />
            <el-table-column prop="recommendation_level" label="推荐等级" min-width="180" />
            <el-table-column prop="data_completeness_score" label="完整性" width="100" />
            <el-table-column prop="benefit_score" label="获益评分" width="100" />
            <el-table-column label="生成时间" min-width="160">
              <template #default="{ row }">{{ formatDateTime(row.generated_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="200">
              <template #default="{ row }">
                <div class="button-row">
                  <el-button text type="primary" @click="rerunHistory(row.patient_id)">重新评估</el-button>
                  <el-button text type="primary" @click="goToReport(row.patient_id)">查看报告</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :total="history.total"
              :page-size="historyPageSize"
              :current-page="historyPage"
              @current-change="handleHistoryPageChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import type { PatientListItem } from '@/api/subjects';
import { fetchPatients } from '@/api/subjects';
import {
  evaluateBatchPatients,
  evaluateSinglePatient,
  fetchRecommendationHistory,
  type BatchEvaluateResponse,
  type RecommendationEvaluationResult,
  type RecommendationHistoryResponse,
} from '@/api/recommendation';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import { formatDateTime } from '@/utils/format';

const router = useRouter();
const activeTab = ref('single');
const patientOptions = ref<PatientListItem[]>([]);
const selectedPatientId = ref<number | undefined>();
const singleResult = ref<RecommendationEvaluationResult | null>(null);
const singleLoading = ref(false);
const batchLoading = ref(false);
const batchKeyword = ref('');
const selectedBatchIds = ref<number[]>([]);
const batchResult = ref<BatchEvaluateResponse | null>(null);
const history = ref<RecommendationHistoryResponse>({
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
});
const historyPage = ref(1);
const historyPageSize = 10;
const historyKeyword = ref('');
const historyLevel = ref<string | undefined>();

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
}

const filteredBatchPatients = computed(() => {
  if (!batchKeyword.value) {
    return patientOptions.value;
  }
  const keyword = batchKeyword.value.toLowerCase();
  return patientOptions.value.filter((item) =>
    `${item.patient_code}${item.anonymized_code}`.toLowerCase().includes(keyword),
  );
});

async function loadPatients() {
  const data = await fetchPatients({ page: 1, page_size: 300 });
  patientOptions.value = data.items;
}

async function runSingle(saveResult: boolean) {
  if (!selectedPatientId.value) {
    ElMessage.warning('请先选择受试者');
    return;
  }

  singleLoading.value = true;
  try {
    singleResult.value = await evaluateSinglePatient(selectedPatientId.value, saveResult);
    ElMessage.success(saveResult ? '推荐结果已生成并保存' : '推荐结果预览已生成');
    await loadHistory();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    singleLoading.value = false;
  }
}

function handleSelectionChange(rows: PatientListItem[]) {
  selectedBatchIds.value = rows.map((item) => item.id);
}

async function runBatch() {
  if (selectedBatchIds.value.length === 0) {
    ElMessage.warning('请至少选择一例受试者');
    return;
  }

  batchLoading.value = true;
  try {
    batchResult.value = await evaluateBatchPatients(selectedBatchIds.value, true);
    ElMessage.success(`批量评估完成，共成功 ${batchResult.value.success_count} 例`);
    await loadHistory();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    batchLoading.value = false;
  }
}

async function loadHistory() {
  history.value = await fetchRecommendationHistory({
    page: historyPage.value,
    page_size: historyPageSize,
    keyword: historyKeyword.value || undefined,
    level: historyLevel.value || undefined,
  });
}

function handleHistoryPageChange(nextPage: number) {
  historyPage.value = nextPage;
  void loadHistory();
}

async function rerunHistory(patientId: number) {
  selectedPatientId.value = patientId;
  activeTab.value = 'single';
  await runSingle(true);
}

function goToReport(patientId: number) {
  void router.push({ path: '/report-center', query: { patientId: String(patientId) } });
}

function goToSubject(patientId: number) {
  void router.push(`/subjects/${patientId}`);
}

onMounted(async () => {
  await Promise.all([loadPatients(), loadHistory()]);
});
</script>

<style scoped>
.recommendation-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-card {
  border-radius: 16px;
}

.metric-box {
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fbff 100%);
}

.metric-box span {
  color: #6d8094;
  font-size: 13px;
}

.metric-box strong {
  display: block;
  margin-top: 10px;
  font-size: 30px;
  color: #173654;
}

.metric-box .small-text {
  font-size: 18px;
  line-height: 1.5;
}

.full-width {
  width: 100%;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.panel-alert,
.result-desc,
.top-gap {
  margin-top: 18px;
}

.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.factor-tag {
  margin-right: 0;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.batch-search {
  width: 320px;
  margin-bottom: 16px;
}

.history-search {
  width: 280px;
}

.history-level {
  width: 180px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 960px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .batch-search,
  .history-search,
  .history-level {
    width: 100%;
  }
}
</style>
