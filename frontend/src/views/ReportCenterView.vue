<template>
  <div class="report-page">
    <DisclaimerBanner />

    <el-tabs v-model="activeTab" class="page-tabs">
      <el-tab-pane label="单例报告预览" name="preview">
        <el-card shadow="never" class="panel-card">
          <template #header><span>报告预览</span></template>
          <div class="toolbar">
            <el-select
              v-model="selectedPatientId"
              filterable
              clearable
              placeholder="请选择已评估受试者"
              class="patient-select"
            >
              <el-option
                v-for="item in patientOptions"
                :key="item.id"
                :label="`${item.patient_code} / ${item.anonymized_code}`"
                :value="item.id"
              />
            </el-select>
            <el-button type="primary" :disabled="!selectedPatientId" :loading="previewLoading" @click="loadPreview">
              预览报告
            </el-button>
            <el-button :disabled="!selectedPatientId" @click="openPrint">打开打印版</el-button>
          </div>

          <div v-if="reportHtml" class="preview-shell">
            <iframe class="preview-frame" :srcdoc="reportHtml"></iframe>
          </div>
          <el-empty v-else description="请选择受试者并生成报告预览" />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="批量导出清单" name="list">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="header-row">
              <span>报告导出清单</span>
              <div class="toolbar">
                <el-input
                  v-model="historyKeyword"
                  placeholder="按患者编号或匿名编号搜索"
                  clearable
                  class="search-input"
                  @keyup.enter="loadHistory"
                  @clear="loadHistory"
                />
                <el-select v-model="historyLevel" clearable placeholder="推荐等级" class="level-select">
                  <el-option label="推荐光干预" value="推荐光干预" />
                  <el-option label="谨慎推荐并短期复评" value="谨慎推荐并短期复评" />
                  <el-option label="暂不直接推荐" value="暂不直接推荐" />
                </el-select>
                <el-button type="primary" plain @click="loadHistory">查询</el-button>
                <el-button type="success" plain @click="handleExportList">导出清单 CSV</el-button>
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
                <div class="toolbar">
                  <el-button text type="primary" @click="previewFromList(row.patient_id)">预览</el-button>
                  <el-button text type="primary" @click="openPrint(row.patient_id)">打印版</el-button>
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
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { fetchPatients, type PatientListItem } from '@/api/subjects';
import {
  downloadReportExportList,
  fetchRecommendationHistory,
  fetchReportHtml,
  openPrintReport,
  type RecommendationHistoryResponse,
} from '@/api/recommendation';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import { formatDateTime } from '@/utils/format';

const route = useRoute();
const activeTab = ref('preview');
const patientOptions = ref<PatientListItem[]>([]);
const selectedPatientId = ref<number | undefined>();
const previewLoading = ref(false);
const reportHtml = ref('');
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

async function loadPatientOptions() {
  const data = await fetchPatients({ page: 1, page_size: 300 });
  patientOptions.value = data.items;
}

async function loadPreview() {
  if (!selectedPatientId.value) {
    ElMessage.warning('请先选择受试者');
    return;
  }
  previewLoading.value = true;
  try {
    reportHtml.value = await fetchReportHtml(selectedPatientId.value, true);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    previewLoading.value = false;
  }
}

function openPrint(patientId?: number) {
  const currentId = patientId || selectedPatientId.value;
  if (!currentId) {
    ElMessage.warning('请先选择受试者');
    return;
  }
  openPrintReport(currentId, true);
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

async function handleExportList() {
  try {
    await downloadReportExportList(historyKeyword.value || undefined, historyLevel.value || undefined);
    ElMessage.success('导出清单已生成');
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  }
}

async function previewFromList(patientId: number) {
  selectedPatientId.value = patientId;
  activeTab.value = 'preview';
  await loadPreview();
}

onMounted(async () => {
  const queryPatientId = Number(route.query.patientId);
  await Promise.all([loadPatientOptions(), loadHistory()]);
  if (!Number.isNaN(queryPatientId) && queryPatientId > 0) {
    selectedPatientId.value = queryPatientId;
    await loadPreview();
  }
});
</script>

<style scoped>
.report-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-card {
  border-radius: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.patient-select {
  width: 320px;
}

.preview-shell {
  margin-top: 20px;
  border: 1px solid #d8e4ef;
  border-radius: 14px;
  overflow: hidden;
}

.preview-frame {
  width: 100%;
  height: 900px;
  border: none;
  background: #fff;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.search-input {
  width: 280px;
}

.level-select {
  width: 180px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 960px) {
  .patient-select,
  .search-input,
  .level-select {
    width: 100%;
  }

  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .preview-frame {
    height: 640px;
  }
}
</style>
