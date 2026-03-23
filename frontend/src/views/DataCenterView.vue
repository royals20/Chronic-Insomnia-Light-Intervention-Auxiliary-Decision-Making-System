<template>
  <div class="page-stack">
    <DisclaimerBanner />

    <PageHeader
      eyebrow="Data Operations"
      title="数据中心"
      description="围绕模板下载、批量导入、质量联动和问题样本过滤构建录入工作流。"
    >
      <template #meta>
        <StatusChip label="导入与录入角色开放" tone="success" />
      </template>
    </PageHeader>

    <SectionCard title="质量联动快照" description="导入完成后，可直接切换到问题样本视图继续补录。">
      <template #actions>
        <ToolbarRow>
          <el-switch
            v-model="affectedOnly"
            active-text="仅看待补录/复核受试者"
            @change="handleAffectedToggle"
          />
          <el-button type="primary" plain @click="loadQualitySnapshot">刷新快照</el-button>
        </ToolbarRow>
      </template>

      <template v-if="qualitySnapshot">
        <div class="stats-grid">
          <MetricCard label="存在问题的受试者" :value="qualitySnapshot.summary.affected_patient_count" description="至少有一条阻塞或警告问题。" />
          <MetricCard label="可建模样本" :value="qualitySnapshot.summary.modeling_ready_patients" description="满足核心建模要素的数据记录。" tone="teal" />
          <MetricCard label="平均完成率" :value="`${qualitySnapshot.summary.average_completion_rate}%`" description="当前样本资料整体完成水平。" tone="sand" />
        </div>

        <el-alert
          :title="`当前共有 ${qualitySnapshot.summary.affected_patient_count} 例受试者存在质量问题，其中阻塞问题 ${qualitySnapshot.summary.blocking_issue_count} 条。`"
          :type="qualitySnapshot.summary.blocking_issue_count > 0 ? 'warning' : 'info'"
          :closable="false"
          show-icon
          class="top-gap"
        >
          <template #default>
            <ToolbarRow>
              <span class="subtle-text">先处理阻塞问题，再进行规则评估或因果训练。</span>
              <el-button type="primary" plain size="small" @click="goToQualityPage">查看质量详情</el-button>
            </ToolbarRow>
          </template>
        </el-alert>
      </template>

      <el-skeleton v-else :rows="2" animated />
    </SectionCard>

    <div class="page-grid two">
      <SectionCard title="模板下载与数据导入" description="支持 CSV / XLSX 模板，按批次写入后端并保留导入历史。">
        <ToolbarRow>
          <el-button type="primary" plain @click="handleDownload('csv')">下载 CSV 模板</el-button>
          <el-button type="success" plain @click="handleDownload('xlsx')">下载 Excel 模板</el-button>
        </ToolbarRow>

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
          <p>建议使用系统模板填写，导入后先刷新质量联动快照。</p>
          <p>对存在阻塞问题的样本，可开启“仅看待补录/复核受试者”快速聚焦。</p>
        </div>

        <el-button
          type="primary"
          class="top-gap"
          :loading="importing"
          :disabled="!selectedFile"
          @click="handleImport"
        >
          开始导入
        </el-button>
      </SectionCard>

      <SectionCard title="最近一次导入结果" description="统计导入成功、更新和失败情况。">
        <template v-if="importResult">
          <div class="compact-grid">
            <MetricCard label="总行数" :value="importResult.summary.total_rows" description="本次处理的原始记录数。" />
            <MetricCard label="成功" :value="importResult.summary.success_count" description="写入成功的记录数。" tone="teal" />
            <MetricCard label="更新" :value="importResult.summary.updated_count" description="命中已有编号并更新的记录数。" tone="sand" />
          </div>

          <el-alert
            :title="importResult.summary.failed_count > 0 ? '存在失败记录，请根据表格修正后重新上传。' : importResult.message"
            :type="importResult.summary.failed_count > 0 ? 'warning' : 'success'"
            :closable="false"
            show-icon
            class="top-gap"
          />

          <el-table
            v-if="importResult.errors.length > 0"
            :data="importResult.errors"
            stripe
            max-height="240"
            class="top-gap"
          >
            <el-table-column prop="row_number" label="行号" width="80" />
            <el-table-column prop="patient_code" label="受试者编号" width="140" />
            <el-table-column prop="message" label="错误说明" min-width="260" />
          </el-table>
        </template>

        <EmptyState
          v-else
          badge="IMPORT"
          title="尚未产生导入结果"
          description="导入完成后，这里会展示本次批次的成功率和失败明细。"
        />
      </SectionCard>
    </div>

    <SectionCard title="数据导入历史" description="按时间倒序查看近期批次。">
      <template #actions>
        <el-button text type="primary" @click="loadImportHistory">刷新</el-button>
      </template>

      <el-table :data="importHistory" stripe>
        <el-table-column prop="occurred_at" label="导入时间" min-width="180" />
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column prop="actor_name" label="操作人" width="120" />
        <el-table-column prop="success_count" label="成功" width="90" />
        <el-table-column prop="failed_count" label="失败" width="90" />
        <el-table-column prop="detail_text" label="说明" min-width="240" />
      </el-table>
    </SectionCard>

    <SectionCard :title="affectedOnly ? '问题受试者列表' : '受试者列表'" description="配合质量快照过滤需要补录的样本。">
      <template #actions>
        <ToolbarRow>
          <el-input
            v-model="keyword"
            placeholder="按受试者编号或匿名编号搜索"
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-button type="primary" plain @click="handleSearch">查询</el-button>
        </ToolbarRow>
      </template>

      <el-table :data="patients" stripe>
        <el-table-column prop="patient_code" label="受试者编号" min-width="130" />
        <el-table-column prop="anonymized_code" label="匿名编号" min-width="130" />
        <el-table-column prop="gender" label="性别" width="90" />
        <el-table-column prop="age" label="年龄" width="90" />
        <el-table-column prop="education_level" label="教育程度" min-width="120" />
        <el-table-column label="资料情况" min-width="180">
          <template #default="{ row }">
            {{ row.has_questionnaire_score && row.has_sleep_metric && row.has_followup_outcome ? '较完整' : '待补录' }}
          </template>
        </el-table-column>
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
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import type { DataQualityResponse } from '@/api/subjects';
import { fetchQualitySummary } from '@/api/subjects';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import EmptyState from '@/components/EmptyState.vue';
import MetricCard from '@/components/MetricCard.vue';
import PageHeader from '@/components/PageHeader.vue';
import SectionCard from '@/components/SectionCard.vue';
import StatusChip from '@/components/StatusChip.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import {
  type ImportHistoryItem,
  type ImportResponse,
  type PatientListItem,
  downloadTemplate,
  fetchImportHistory,
  fetchPatients,
  uploadPatientFile,
} from '@/api/dataCenter';

const route = useRoute();
const router = useRouter();
const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const importing = ref(false);
const importResult = ref<ImportResponse | null>(null);
const importHistory = ref<ImportHistoryItem[]>([]);
const qualitySnapshot = ref<DataQualityResponse | null>(null);
const patients = ref<PatientListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const keyword = ref('');
const affectedOnly = ref(route.query.quality === 'attention');

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
    ids: affectedOnly.value ? qualitySnapshot.value?.affected_patient_ids : undefined,
  });
  patients.value = data.items;
  total.value = data.total;
}

async function loadImportHistory() {
  importHistory.value = await fetchImportHistory(10);
}

async function loadQualitySnapshot() {
  qualitySnapshot.value = await fetchQualitySummary();
  await loadPatients();
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
    await Promise.all([loadPatients(), loadImportHistory(), loadQualitySnapshot()]);
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

async function handleAffectedToggle() {
  page.value = 1;
  await router.replace({
    path: '/data-center',
    query: affectedOnly.value ? { quality: 'attention' } : {},
  });
  await loadPatients();
}

function goToQualityPage() {
  void router.push('/data-quality');
}

onMounted(async () => {
  await Promise.all([loadImportHistory(), loadQualitySnapshot()]);
});
</script>

<style scoped>
.upload-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-lg);
  background: rgba(248, 251, 255, 0.8);
}

.hidden-input {
  display: none;
}

.file-name {
  color: var(--ink-soft);
}

.upload-tip {
  margin-top: 16px;
  color: var(--ink-soft);
  line-height: 1.8;
}

.upload-tip p {
  margin: 0;
}

.top-gap {
  margin-top: 18px;
}

.search-input {
  width: min(320px, 100%);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
