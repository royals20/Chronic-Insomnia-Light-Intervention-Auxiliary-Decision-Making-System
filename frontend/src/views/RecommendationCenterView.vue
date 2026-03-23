<template>
  <div class="page-stack recommendation-page">
    <DisclaimerBanner />

    <InsightHero
      eyebrow="Recommendation Lab"
      title="光干预获益评估驾驶舱"
      description="将规则评估流程组织成单例、批量和历史追溯三条路径，让答辩时先看到结论，再追溯依据与动作。"
    >
      <template #meta>
        <DataBadge label="规则/评分引擎 V1" tone="primary" />
        <DataBadge label="单例 / 批量 / 历史追溯" tone="info" />
        <DataBadge label="仅供科研辅助" tone="warning" />
      </template>

      <template #actions>
        <ToolbarRow>
          <el-button type="primary" @click="activeTab = 'single'">开始单例评估</el-button>
          <el-button plain @click="activeTab = 'batch'">切换批量评估</el-button>
          <el-button plain @click="activeTab = 'history'">查看历史结果</el-button>
          <el-button @click="goToModelCenter">前往模型中心</el-button>
        </ToolbarRow>
      </template>

      <template #aside>
        <div class="recommendation-hero-aside">
          <div class="key-value-grid">
            <div class="key-value-card">
              <span>候选受试者</span>
              <strong>{{ patientOptions.length }}</strong>
            </div>
            <div class="key-value-card">
              <span>历史记录</span>
              <strong>{{ history.total }}</strong>
            </div>
          </div>
          <p class="recommendation-hero-aside__text">
            当前推荐流程适合科研展示与快速筛查；若需解释处理效应和特征贡献，请切换到模型中心或因果结果页。
          </p>
        </div>
      </template>
    </InsightHero>

    <InsightSummaryStrip :items="summaryItems" />

    <el-tabs v-model="activeTab" class="page-tabs">
      <el-tab-pane label="单例评估" name="single">
        <div class="analysis-grid three">
          <NarrativePanel
            title="1. 选择受试者"
            description="从受试者库选定单例，并快速判断资料是否足够支撑本次规则评估。"
          >
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

              <div v-if="selectedPatient" class="subject-brief">
                <div>
                  <span>患者编号</span>
                  <strong>{{ selectedPatient.patient_code }}</strong>
                </div>
                <div>
                  <span>匿名编号</span>
                  <strong>{{ selectedPatient.anonymized_code }}</strong>
                </div>
                <div>
                  <span>年龄 / 性别</span>
                  <strong>{{ selectedPatient.age ?? '--' }} / {{ selectedPatient.gender || '--' }}</strong>
                </div>
              </div>

              <div class="tag-cluster top-gap">
                <DataBadge v-bind="selectedPatientMaterialBadge" />
                <DataBadge
                  :label="selectedPatient?.has_questionnaire_score ? '量表已录入' : '量表待补录'"
                  :tone="selectedPatient?.has_questionnaire_score ? 'success' : 'warning'"
                />
                <DataBadge
                  :label="selectedPatient?.has_sleep_metric ? '睡眠指标已录入' : '睡眠指标待补录'"
                  :tone="selectedPatient?.has_sleep_metric ? 'success' : 'warning'"
                />
              </div>
            </el-form>

            <template #footer>
              <ToolbarRow>
                <el-button type="primary" :disabled="!selectedPatientId" :loading="singleLoading" @click="runSingle(true)">
                  生成并保存推荐
                </el-button>
                <el-button :disabled="!selectedPatientId" :loading="singleLoading" @click="runSingle(false)">
                  仅预览
                </el-button>
              </ToolbarRow>
            </template>
          </NarrativePanel>

          <NarrativePanel
            title="2. 推荐结论"
            description="优先显示结论等级、分值和一句话说明，适合投影环境快速讲解。"
            tone="accent"
          >
            <template v-if="singleResult">
              <div class="result-highlight">
                <DataBadge v-bind="singleRecommendationBadge" strong />
                <h3>{{ singleResult.recommendation_level }}</h3>
                <p>{{ singleResult.explanation_text }}</p>
              </div>

              <div class="key-value-grid top-gap">
                <div class="key-value-card">
                  <span>获益评分</span>
                  <strong>{{ singleResult.benefit_score }}</strong>
                </div>
                <div class="key-value-card">
                  <span>数据完整性</span>
                  <strong>{{ singleResult.data_completeness_score }}</strong>
                </div>
                <div class="key-value-card">
                  <span>引擎版本</span>
                  <strong>{{ `${singleResult.engine_name} / ${singleResult.engine_version}` }}</strong>
                </div>
              </div>
            </template>

            <EmptyState
              v-else
              badge="SINGLE"
              title="尚未生成单例结论"
              description="在左侧选择受试者后执行评估，这里会突出展示当前推荐等级、分值和摘要说明。"
            />
          </NarrativePanel>

          <NarrativePanel
            title="3. 证据与动作"
            description="解释关键影响因素、使用限制，并给出下一步查看报告或回看个体信息的动作。"
          >
            <template v-if="singleResult">
              <div class="evidence-block">
                <span class="evidence-block__title">关键影响因素</span>
                <div class="factor-list">
                  <div v-for="item in singleResult.key_factors" :key="item" class="factor-item">{{ item }}</div>
                </div>
              </div>

              <div class="evidence-block">
                <span class="evidence-block__title">使用限制</span>
                <ul class="plain-list">
                  <li v-for="item in singleResult.usage_limitations" :key="item">{{ item }}</li>
                </ul>
              </div>
            </template>

            <template #footer>
              <ToolbarRow>
                <el-button
                  type="primary"
                  plain
                  :disabled="!singleResult"
                  @click="singleResult && goToReport(singleResult.patient_id)"
                >
                  查看报告
                </el-button>
                <el-button
                  plain
                  :disabled="!singleResult"
                  @click="singleResult && goToSubject(singleResult.patient_id)"
                >
                  查看受试者详情
                </el-button>
              </ToolbarRow>
            </template>
          </NarrativePanel>
        </div>
      </el-tab-pane>

      <el-tab-pane label="批量评估" name="batch">
        <NarrativePanel title="批量评估候选列表" description="筛选受试者后批量生成推荐，并在底部粘性执行条中持续显示当前选择状态。">
          <template #actions>
            <ToolbarRow>
              <el-input
                v-model="batchKeyword"
                placeholder="按患者编号或匿名编号过滤"
                clearable
                class="batch-search"
              />
              <DataBadge :label="`已选 ${selectedBatchIds.length} 例`" :tone="selectedBatchIds.length > 0 ? 'primary' : 'neutral'" />
            </ToolbarRow>
          </template>

          <el-table :data="filteredBatchPatients" stripe @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="52" />
            <el-table-column prop="patient_code" label="患者编号" min-width="120" />
            <el-table-column prop="anonymized_code" label="匿名编号" min-width="120" />
            <el-table-column prop="gender" label="性别" width="80" />
            <el-table-column prop="age" label="年龄" width="80" />
            <el-table-column label="资料状态" min-width="140">
              <template #default="{ row }">
                <DataBadge v-bind="batchRowBadge(row)" size="sm" />
              </template>
            </el-table-column>
          </el-table>
        </NarrativePanel>

        <InsightSummaryStrip v-if="batchResult" :items="batchSummaryItems" />

        <NarrativePanel
          v-if="batchResult?.errors?.length"
          title="批量执行提示"
          description="失败记录保留在错误列表中，便于答辩时解释为什么需要先补录数据。"
          tone="warning"
        >
          <ul class="plain-list">
            <li v-for="item in batchResult.errors" :key="item">{{ item }}</li>
          </ul>
        </NarrativePanel>

        <div class="sticky-bottom-bar">
          <div class="sticky-bottom-bar__content">
            <div>
              <strong class="sticky-bottom-bar__title">批量执行条</strong>
              <p class="sticky-bottom-bar__text">
                当前已选择 {{ selectedBatchIds.length }} 例受试者，执行后会自动写入历史记录并刷新查询结果。
              </p>
            </div>

            <ToolbarRow>
              <el-button type="primary" :disabled="selectedBatchIds.length === 0" :loading="batchLoading" @click="runBatch">
                批量生成并保存
              </el-button>
              <el-button plain @click="activeTab = 'history'">查看历史结果</el-button>
            </ToolbarRow>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史结果查询" name="history">
        <NarrativePanel title="历史推荐结果" description="在顶部完成筛选，在表格中点击记录后直接打开右侧抽屉查看详情。">
          <template #actions>
            <div class="history-controls">
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
          </template>

          <el-table :data="history.items" stripe @row-click="openHistoryDetail">
            <el-table-column prop="patient_code" label="患者编号" min-width="120" />
            <el-table-column prop="anonymized_code" label="匿名编号" min-width="120" />
            <el-table-column label="推荐等级" min-width="190">
              <template #default="{ row }">
                <DataBadge v-bind="badgeForRecommendationLevel(row.recommendation_level)" size="sm" />
              </template>
            </el-table-column>
            <el-table-column prop="data_completeness_score" label="完整性" width="100" />
            <el-table-column prop="benefit_score" label="获益评分" width="100" />
            <el-table-column label="生成时间" min-width="160">
              <template #default="{ row }">{{ formatDateTime(row.generated_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="200">
              <template #default="{ row }">
                <ToolbarRow>
                  <el-button text type="primary" @click.stop="openHistoryDetail(row)">查看详情</el-button>
                  <el-button text type="primary" @click.stop="rerunHistory(row.patient_id)">重新评估</el-button>
                </ToolbarRow>
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
        </NarrativePanel>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="historyDrawerVisible" size="420px" :with-header="false">
      <div v-if="activeHistoryItem" class="history-drawer">
        <span class="history-drawer__eyebrow">Recommendation Snapshot</span>
        <h3>{{ activeHistoryItem.patient_code }} / {{ activeHistoryItem.anonymized_code }}</h3>
        <p>{{ activeHistoryItem.explanation_text || '当前记录未保存详细说明。' }}</p>

        <div class="tag-cluster">
          <DataBadge v-bind="badgeForRecommendationLevel(activeHistoryItem.recommendation_level)" />
          <DataBadge
            :label="activeHistoryItem.engine_name ? `${activeHistoryItem.engine_name} / ${activeHistoryItem.engine_version || '-'}` : '引擎未记录'"
            tone="primary"
          />
        </div>

        <div class="history-drawer__metrics">
          <div>
            <span>完整性</span>
            <strong>{{ activeHistoryItem.data_completeness_score ?? '--' }}</strong>
          </div>
          <div>
            <span>获益评分</span>
            <strong>{{ activeHistoryItem.benefit_score ?? '--' }}</strong>
          </div>
          <div>
            <span>生成时间</span>
            <strong>{{ formatDateTime(activeHistoryItem.generated_at) }}</strong>
          </div>
        </div>

        <ToolbarRow class="history-drawer__actions">
          <el-button type="primary" plain @click="rerunHistory(activeHistoryItem.patient_id)">重新评估</el-button>
          <el-button plain @click="goToReport(activeHistoryItem.patient_id)">查看报告</el-button>
          <el-button plain @click="goToSubject(activeHistoryItem.patient_id)">受试者详情</el-button>
        </ToolbarRow>
      </div>
    </el-drawer>
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
  type RecommendationHistoryItem,
  type RecommendationHistoryResponse,
} from '@/api/recommendation';
import DataBadge from '@/components/DataBadge.vue';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import EmptyState from '@/components/EmptyState.vue';
import InsightHero from '@/components/InsightHero.vue';
import InsightSummaryStrip from '@/components/InsightSummaryStrip.vue';
import NarrativePanel from '@/components/NarrativePanel.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import {
  badgeForCompleteness,
  badgeForPatientMaterialReady,
  badgeForRecommendationLevel,
} from '@/utils/dataBadges';
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
const historyDrawerVisible = ref(false);
const activeHistoryItem = ref<RecommendationHistoryItem | null>(null);

const selectedPatient = computed(() =>
  patientOptions.value.find((item) => item.id === selectedPatientId.value),
);

const selectedPatientMaterialBadge = computed(() =>
  badgeForPatientMaterialReady(
    !!selectedPatient.value?.has_questionnaire_score && !!selectedPatient.value?.has_sleep_metric,
  ),
);

const singleRecommendationBadge = computed(() =>
  badgeForRecommendationLevel(singleResult.value?.recommendation_level),
);

const summaryItems = computed(() => [
  {
    label: '候选受试者',
    value: patientOptions.value.length,
    description: '可直接参与单例或批量评估。',
    tone: 'primary' as const,
  },
  {
    label: '单例当前状态',
    value: singleResult.value?.recommendation_level || '待评估',
    description: singleResult.value ? '已生成最新推荐结论。' : '尚未生成单例结论。',
    tone: singleResult.value ? singleRecommendationBadge.value.tone : ('neutral' as const),
  },
  {
    label: '批量已选样本',
    value: selectedBatchIds.value.length,
    description: '底部执行条会持续显示当前选择。',
    tone: selectedBatchIds.value.length > 0 ? ('info' as const) : ('neutral' as const),
  },
  {
    label: '历史记录数',
    value: history.value.total,
    description: '支持结果回看与重新评估。',
    tone: 'warning' as const,
  },
]);

const batchSummaryItems = computed(() => {
  if (!batchResult.value) {
    return [];
  }
  return [
    {
      label: '请求样本数',
      value: batchResult.value.total_requested,
      description: '本次批量评估发起的受试者数量。',
      tone: 'primary' as const,
    },
    {
      label: '成功数',
      value: batchResult.value.success_count,
      description: '成功生成并保存推荐结果的记录。',
      tone: 'success' as const,
    },
    {
      label: '失败数',
      value: batchResult.value.failed_count,
      description: '失败原因会保留在下方提示中。',
      tone: batchResult.value.failed_count > 0 ? ('danger' as const) : ('neutral' as const),
    },
  ];
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

const filteredBatchPatients = computed(() => {
  if (!batchKeyword.value) {
    return patientOptions.value;
  }
  const keyword = batchKeyword.value.toLowerCase();
  return patientOptions.value.filter((item) =>
    `${item.patient_code}${item.anonymized_code}`.toLowerCase().includes(keyword),
  );
});

function batchRowBadge(row: PatientListItem) {
  return badgeForPatientMaterialReady(!!row.has_questionnaire_score && !!row.has_sleep_metric);
}

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
  historyDrawerVisible.value = false;
  await runSingle(true);
}

function openHistoryDetail(row: RecommendationHistoryItem) {
  activeHistoryItem.value = row;
  historyDrawerVisible.value = true;
}

function goToReport(patientId: number) {
  void router.push({ path: '/report-center', query: { patientId: String(patientId) } });
}

function goToSubject(patientId: number) {
  void router.push(`/subjects/${patientId}`);
}

function goToModelCenter() {
  void router.push('/model-center');
}

onMounted(async () => {
  await Promise.all([loadPatients(), loadHistory()]);
});
</script>

<style scoped>
.recommendation-hero-aside {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    linear-gradient(180deg, rgba(13, 95, 111, 0.08), rgba(13, 95, 111, 0.03)),
    rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(13, 95, 111, 0.1);
}

.recommendation-hero-aside__text {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.top-gap {
  margin-top: 18px;
}

.subject-brief {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  margin-top: 10px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: rgba(247, 250, 252, 0.92);
  border: 1px solid var(--line-soft);
}

.subject-brief span,
.evidence-block__title {
  display: block;
  color: var(--ink-muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subject-brief strong {
  display: block;
  margin-top: 8px;
  color: var(--ink-strong);
}

.result-highlight {
  padding: 22px;
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top right, rgba(13, 95, 111, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 248, 250, 0.94));
  border: 1px solid rgba(13, 95, 111, 0.12);
}

.result-highlight h3 {
  margin: 16px 0 10px;
  color: var(--ink-strong);
  font-size: clamp(28px, 2.3vw, 36px);
  line-height: 1.08;
}

.result-highlight p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 15px;
  line-height: 1.8;
}

.evidence-block + .evidence-block {
  margin-top: 20px;
}

.factor-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.factor-item {
  padding: 14px 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: rgba(248, 251, 255, 0.76);
  color: var(--ink-soft);
  line-height: 1.7;
}

.batch-search {
  width: 320px;
}

.sticky-bottom-bar__title {
  display: block;
  color: var(--ink-strong);
}

.sticky-bottom-bar__text {
  margin: 6px 0 0;
  color: var(--ink-soft);
}

.history-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
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

.history-drawer {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 22px;
}

.history-drawer__eyebrow {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.history-drawer h3 {
  margin: 0;
  color: var(--ink-strong);
  font-size: 28px;
  line-height: 1.12;
}

.history-drawer p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.history-drawer__metrics {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.history-drawer__metrics > div {
  padding: 16px;
  border-radius: var(--radius-lg);
  background: rgba(247, 250, 252, 0.94);
  border: 1px solid var(--line-soft);
}

.history-drawer__metrics span {
  display: block;
  color: var(--ink-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.history-drawer__metrics strong {
  display: block;
  margin-top: 10px;
  color: var(--ink-strong);
}

.history-drawer__actions {
  padding-top: 4px;
}

@media (max-width: 960px) {
  .batch-search,
  .history-search,
  .history-level {
    width: 100%;
  }
}
</style>
