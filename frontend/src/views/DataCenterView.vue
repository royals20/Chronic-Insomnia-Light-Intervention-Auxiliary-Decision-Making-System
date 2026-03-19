<template>
  <div class="data-center-page">
    <DisclaimerBanner />

    <el-row :gutter="20" class="top-row">
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>模板下载与数据导入</span>
              <el-tag type="info">支持 CSV / XLSX</el-tag>
            </div>
          </template>

          <div class="action-group">
            <el-button type="primary" plain @click="handleDownload('csv')">下载 CSV 模板</el-button>
            <el-button type="success" plain @click="handleDownload('xlsx')">下载 Excel 模板</el-button>
          </div>

          <div class="upload-box">
            <input
              ref="fileInputRef"
              type="file"
              accept=".csv,.xlsx"
              class="hidden-input"
              @change="handleFileChange"
            />
            <el-button type="primary" @click="triggerFileSelect">选择导入文件</el-button>
            <span class="file-name">{{ selectedFile?.name || '尚未选择文件' }}</span>
          </div>

          <div class="upload-tip">
            <p>建议使用系统模板填写，患者编号与匿名编号为必填列。</p>
            <p>仅供科研辅助，不替代临床诊断与治疗。</p>
          </div>

          <el-button
            type="primary"
            class="import-button"
            :loading="importing"
            :disabled="!selectedFile"
            @click="handleImport"
          >
            开始导入
          </el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>最近一次导入结果</span>
              <el-tag :type="importResult ? (importResult.summary.failed_count > 0 ? 'warning' : 'success') : 'info'">
                {{ importResult ? '已更新' : '等待导入' }}
              </el-tag>
            </div>
          </template>

          <div v-if="importResult" class="result-wrap">
            <el-row :gutter="16">
              <el-col :xs="12" :md="6">
                <div class="result-stat">
                  <span>总行数</span>
                  <strong>{{ importResult.summary.total_rows }}</strong>
                </div>
              </el-col>
              <el-col :xs="12" :md="6">
                <div class="result-stat">
                  <span>成功</span>
                  <strong>{{ importResult.summary.success_count }}</strong>
                </div>
              </el-col>
              <el-col :xs="12" :md="6">
                <div class="result-stat">
                  <span>新建</span>
                  <strong>{{ importResult.summary.created_count }}</strong>
                </div>
              </el-col>
              <el-col :xs="12" :md="6">
                <div class="result-stat">
                  <span>更新</span>
                  <strong>{{ importResult.summary.updated_count }}</strong>
                </div>
              </el-col>
            </el-row>

            <el-alert
              v-if="importResult.summary.failed_count > 0"
              title="导入存在失败记录，请根据下表修正后重新上传。"
              type="warning"
              :closable="false"
              show-icon
              class="result-alert"
            />

            <el-alert
              v-else
              :title="importResult.message"
              type="success"
              :closable="false"
              show-icon
              class="result-alert"
            />

            <el-table
              v-if="importResult.errors.length > 0"
              :data="importResult.errors"
              stripe
              max-height="220"
            >
              <el-table-column prop="row_number" label="行号" width="80" />
              <el-table-column prop="patient_code" label="患者编号" width="120" />
              <el-table-column prop="message" label="错误说明" min-width="240" />
            </el-table>
          </div>

          <el-empty v-else description="尚未产生导入结果" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="panel-header">
          <span>数据导入历史</span>
          <el-button text type="primary" @click="loadImportHistory">刷新</el-button>
        </div>
      </template>

      <el-table :data="importHistory" stripe>
        <el-table-column prop="occurred_at" label="导入时间" min-width="170" />
        <el-table-column prop="file_name" label="文件名" min-width="180" />
        <el-table-column prop="actor_name" label="操作人" width="120" />
        <el-table-column prop="success_count" label="成功" width="80" />
        <el-table-column prop="failed_count" label="失败" width="80" />
        <el-table-column prop="detail_text" label="说明" min-width="220" />
      </el-table>
    </el-card>

    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="panel-header">
          <span>患者列表</span>
          <div class="header-tools">
            <el-input
              v-model="keyword"
              placeholder="按患者编号或匿名编号搜索"
              clearable
              class="search-input"
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            />
            <el-button type="primary" plain @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="patients" stripe>
        <el-table-column prop="patient_code" label="患者编号" min-width="120" />
        <el-table-column prop="anonymized_code" label="匿名编号" min-width="120" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="age" label="年龄" width="80" />
        <el-table-column prop="education_level" label="教育程度" min-width="120" />
        <el-table-column prop="updated_at" label="更新时间" min-width="180" />
        <el-table-column prop="remarks" label="备注" min-width="180" />
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { onMounted, ref } from 'vue';

import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import {
  type ImportHistoryItem,
  type ImportResponse,
  type PatientListItem,
  downloadTemplate,
  fetchImportHistory,
  fetchPatients,
  uploadPatientFile,
} from '@/api/dataCenter';

const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const importing = ref(false);
const importResult = ref<ImportResponse | null>(null);
const importHistory = ref<ImportHistoryItem[]>([]);
const patients = ref<PatientListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const keyword = ref('');

function triggerFileSelect() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] || null;
}

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
}

async function handleDownload(format: 'csv' | 'xlsx') {
  try {
    await downloadTemplate(format);
    ElMessage.success(`模板下载成功：${format.toUpperCase()}`);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  }
}

async function loadPatients() {
  const data = await fetchPatients({
    page: page.value,
    page_size: pageSize,
    keyword: keyword.value || undefined,
  });
  patients.value = data.items;
  total.value = data.total;
}

async function loadImportHistory() {
  importHistory.value = await fetchImportHistory(10);
}

async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择待导入文件');
    return;
  }

  importing.value = true;
  try {
    importResult.value = await uploadPatientFile(selectedFile.value);
    ElMessage.success(importResult.value.message);
    await Promise.all([loadPatients(), loadImportHistory()]);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    importing.value = false;
  }
}

async function handleSearch() {
  page.value = 1;
  await loadPatients();
}

async function handlePageChange(nextPage: number) {
  page.value = nextPage;
  await loadPatients();
}

onMounted(async () => {
  await Promise.all([loadPatients(), loadImportHistory()]);
});
</script>

<style scoped>
.data-center-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.top-row {
  margin-bottom: 0;
}

.panel-card,
.section-card {
  border-radius: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px;
  border: 1px dashed #cfdbe8;
  border-radius: 12px;
  background: #f8fbff;
}

.hidden-input {
  display: none;
}

.file-name {
  color: #607487;
  font-size: 14px;
}

.upload-tip {
  margin-top: 16px;
  color: #6c7f92;
  line-height: 1.8;
  font-size: 14px;
}

.upload-tip p {
  margin: 0;
}

.import-button {
  margin-top: 18px;
}

.result-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-stat {
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #f7fbff 100%);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-stat span {
  color: #688198;
  font-size: 13px;
}

.result-stat strong {
  color: #123c65;
  font-size: 28px;
}

.result-alert {
  margin-top: 4px;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 260px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 960px) {
  .header-tools {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-input {
    width: 100%;
  }
}
</style>
