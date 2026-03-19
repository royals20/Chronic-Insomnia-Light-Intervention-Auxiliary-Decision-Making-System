<template>
  <div class="settings-page">
    <DisclaimerBanner />

    <el-row :gutter="20">
      <el-col :xs="24" :xl="10">
        <el-card shadow="never" class="panel-card">
          <template #header><span>规则阈值配置</span></template>
          <template v-if="config">
            <el-form label-position="top">
              <el-form-item label="引擎名称">
                <el-input v-model="config.engine_name" />
              </el-form-item>
              <el-form-item label="引擎版本">
                <el-input v-model="config.engine_version" />
              </el-form-item>
              <el-form-item label="模型版本名称">
                <el-input v-model="config.model_version_name" />
              </el-form-item>
              <el-form-item label="基础获益分">
                <el-input-number v-model="config.base_benefit_score" :min="0" :max="100" class="full-width" />
              </el-form-item>

              <el-divider>推荐阈值</el-divider>

              <el-form-item label="直接推荐最低分">
                <el-input-number v-model="config.thresholds.recommend_min_score" :min="0" :max="100" class="full-width" />
              </el-form-item>
              <el-form-item label="谨慎推荐最低分">
                <el-input-number v-model="config.thresholds.cautious_min_score" :min="0" :max="100" class="full-width" />
              </el-form-item>
              <el-form-item label="直接推荐最小完整性">
                <el-input-number v-model="config.thresholds.min_completeness_for_recommend" :min="0" :max="100" class="full-width" />
              </el-form-item>
              <el-form-item label="谨慎推荐最小完整性">
                <el-input-number v-model="config.thresholds.min_completeness_for_cautious" :min="0" :max="100" class="full-width" />
              </el-form-item>

              <div class="toolbar">
                <el-button type="primary" :loading="saving" @click="handleSaveForm">保存表单配置</el-button>
                <el-button @click="syncJsonFromConfig">同步到 JSON</el-button>
              </div>
            </el-form>
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="14">
        <el-card shadow="never" class="panel-card">
          <template #header><span>规则清单与高级 JSON 编辑</span></template>
          <template v-if="config">
            <el-table :data="config.score_rules" stripe max-height="320">
              <el-table-column prop="label" label="规则名称" min-width="130" />
              <el-table-column prop="field_path" label="字段路径" min-width="160" />
              <el-table-column prop="operator" label="运算符" width="90" />
              <el-table-column prop="value" label="阈值" width="90" />
              <el-table-column prop="score_delta" label="分值变化" width="100" />
            </el-table>

            <el-divider>高级 JSON</el-divider>

            <el-input
              v-model="configJsonText"
              type="textarea"
              :rows="18"
              placeholder="此处可直接编辑完整规则 JSON"
            />

            <div class="toolbar top-gap">
              <el-button type="primary" plain :loading="saving" @click="handleSaveJson">按 JSON 保存</el-button>
              <el-button @click="loadConfig">重新加载</el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { onMounted, ref } from 'vue';

import type { RecommendationConfig } from '@/api/recommendation';
import { fetchRecommendationConfig, saveRecommendationConfig } from '@/api/recommendation';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';

const config = ref<RecommendationConfig | null>(null);
const configJsonText = ref('');
const saving = ref(false);

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
}

function syncJsonFromConfig() {
  if (!config.value) {
    return;
  }
  configJsonText.value = JSON.stringify(config.value, null, 2);
}

async function loadConfig() {
  config.value = await fetchRecommendationConfig();
  syncJsonFromConfig();
}

async function handleSaveForm() {
  if (!config.value) {
    return;
  }
  saving.value = true;
  try {
    config.value = await saveRecommendationConfig(config.value);
    syncJsonFromConfig();
    ElMessage.success('规则阈值配置已保存');
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    saving.value = false;
  }
}

async function handleSaveJson() {
  saving.value = true;
  try {
    const parsed = JSON.parse(configJsonText.value) as RecommendationConfig;
    config.value = await saveRecommendationConfig(parsed);
    syncJsonFromConfig();
    ElMessage.success('高级 JSON 配置已保存');
  } catch (error) {
    if (error instanceof SyntaxError) {
      ElMessage.error('JSON 格式有误，请先修正后再保存');
    } else {
      ElMessage.error(extractErrorMessage(error));
    }
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadConfig();
});
</script>

<style scoped>
.settings-page {
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

.top-gap {
  margin-top: 16px;
}

.full-width {
  width: 100%;
}
</style>
