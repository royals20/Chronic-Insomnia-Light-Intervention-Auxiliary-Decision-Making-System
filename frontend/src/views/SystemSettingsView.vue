<template>
  <div class="page-stack">
    <DisclaimerBanner />

    <PageHeader
      eyebrow="Admin Control"
      title="系统设置"
      description="本页仅管理员可访问。推荐规则和用户管理拆分为独立标签区，避免配置与权限操作混在一起。"
    >
      <template #meta>
        <StatusChip label="管理员专属" tone="warning" />
      </template>
    </PageHeader>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="推荐规则配置" name="rules">
        <div class="page-grid two">
          <SectionCard title="表单配置" description="适合直接调整阈值和引擎元信息。">
            <template v-if="config">
              <el-form label-position="top">
                <el-form-item label="引擎名称">
                  <el-input v-model="config.engine_name" />
                </el-form-item>
                <el-form-item label="引擎版本">
                  <el-input v-model="config.engine_version" />
                </el-form-item>
                <el-form-item label="模型版本名">
                  <el-input v-model="config.model_version_name" />
                </el-form-item>
                <el-form-item label="基础获益分">
                  <el-input-number v-model="config.base_benefit_score" :min="0" :max="100" class="full-width" />
                </el-form-item>

                <div class="compact-grid">
                  <el-form-item label="直接推荐最低分">
                    <el-input-number v-model="config.thresholds.recommend_min_score" :min="0" :max="100" class="full-width" />
                  </el-form-item>
                  <el-form-item label="谨慎推荐最低分">
                    <el-input-number v-model="config.thresholds.cautious_min_score" :min="0" :max="100" class="full-width" />
                  </el-form-item>
                  <el-form-item label="直接推荐最低完整度">
                    <el-input-number v-model="config.thresholds.min_completeness_for_recommend" :min="0" :max="100" class="full-width" />
                  </el-form-item>
                  <el-form-item label="谨慎推荐最低完整度">
                    <el-input-number v-model="config.thresholds.min_completeness_for_cautious" :min="0" :max="100" class="full-width" />
                  </el-form-item>
                </div>

                <ToolbarRow>
                  <el-button type="primary" :loading="saving" @click="handleSaveForm">保存表单配置</el-button>
                  <el-button @click="syncJsonFromConfig">同步到 JSON</el-button>
                </ToolbarRow>
              </el-form>
            </template>
          </SectionCard>

          <SectionCard title="规则清单与 JSON" description="适合高级编辑和完整快照管理。">
            <template v-if="config">
              <el-table :data="config.score_rules" stripe max-height="300">
                <el-table-column prop="label" label="规则名称" min-width="130" />
                <el-table-column prop="field_path" label="字段路径" min-width="160" />
                <el-table-column prop="operator" label="运算符" width="90" />
                <el-table-column prop="value" label="阈值" width="90" />
                <el-table-column prop="score_delta" label="分值变化" width="100" />
              </el-table>

              <el-input
                v-model="configJsonText"
                type="textarea"
                :rows="18"
                placeholder="此处可直接编辑完整规则 JSON"
                class="top-gap"
              />

              <ToolbarRow class="top-gap">
                <el-button type="primary" plain :loading="saving" @click="handleSaveJson">按 JSON 保存</el-button>
                <el-button @click="loadConfig">重新加载</el-button>
              </ToolbarRow>
            </template>
          </SectionCard>
        </div>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <SectionCard title="系统用户" description="支持创建用户、修改角色、停用启用和重置密码。">
          <template #actions>
            <ToolbarRow>
              <el-button type="primary" plain @click="openCreateDialog">新增用户</el-button>
              <el-button @click="loadUsers">刷新列表</el-button>
            </ToolbarRow>
          </template>

          <el-table :data="users" stripe v-loading="usersLoading">
            <el-table-column prop="username" label="用户名" min-width="140" />
            <el-table-column prop="full_name" label="姓名" min-width="140" />
            <el-table-column label="角色" width="120">
              <template #default="{ row }">
                <StatusChip :label="roleLabel(row.role)" tone="primary" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <StatusChip :label="row.is_active ? '启用' : '停用'" :tone="row.is_active ? 'success' : 'danger'" />
              </template>
            </el-table-column>
            <el-table-column prop="last_login_at" label="最近登录" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.last_login_at) }}</template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="260">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button text type="primary" @click="openEditDialog(row)">编辑</el-button>
                  <el-button text type="primary" @click="openResetPasswordDialog(row)">重置密码</el-button>
                  <el-button text :type="row.is_active ? 'danger' : 'primary'" @click="handleToggleUserActive(row)">
                    {{ row.is_active ? '停用' : '启用' }}
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </SectionCard>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="userDialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="userForm" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" :disabled="Boolean(editingUser)" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.full_name" />
        </el-form-item>
        <div class="compact-grid">
          <el-form-item label="角色">
            <el-select v-model="userForm.role" class="full-width">
              <el-option label="管理员" value="admin" />
              <el-option label="研究员" value="researcher" />
              <el-option label="录入员" value="data_entry" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="userForm.is_active" />
          </el-form-item>
        </div>
        <el-form-item v-if="!editingUser" label="初始密码">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="userSaving" @click="submitUserForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="460px">
      <el-form label-position="top">
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordSaving" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { onMounted, reactive, ref } from 'vue';

import type { UserRole } from '@/auth/access';
import { roleLabel } from '@/auth/access';
import type { RecommendationConfig } from '@/api/recommendation';
import { fetchRecommendationConfig, saveRecommendationConfig } from '@/api/recommendation';
import type { UserRecord } from '@/api/users';
import { createUser, fetchUsers, resetUserPassword, toggleUserActive, updateUser } from '@/api/users';
import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import PageHeader from '@/components/PageHeader.vue';
import SectionCard from '@/components/SectionCard.vue';
import StatusChip from '@/components/StatusChip.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import { formatDateTime } from '@/utils/format';

const activeTab = ref('rules');
const config = ref<RecommendationConfig | null>(null);
const configJsonText = ref('');
const saving = ref(false);

const users = ref<UserRecord[]>([]);
const usersLoading = ref(false);
const userSaving = ref(false);
const passwordSaving = ref(false);
const editingUser = ref<UserRecord | null>(null);
const passwordTargetUser = ref<UserRecord | null>(null);
const userDialogVisible = ref(false);
const passwordDialogVisible = ref(false);

const userForm = reactive({
  username: '',
  full_name: '',
  role: 'researcher' as UserRole,
  password: '',
  is_active: true,
});

const passwordForm = reactive({
  newPassword: '',
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
    ElMessage.success('规则配置已保存');
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
    ElMessage.success('JSON 配置已保存');
  } catch (error) {
    if (error instanceof SyntaxError) {
      ElMessage.error('JSON 格式有误，请修正后再保存');
    } else {
      ElMessage.error(extractErrorMessage(error));
    }
  } finally {
    saving.value = false;
  }
}

async function loadUsers() {
  usersLoading.value = true;
  try {
    users.value = await fetchUsers();
  } finally {
    usersLoading.value = false;
  }
}

function resetUserForm() {
  userForm.username = '';
  userForm.full_name = '';
  userForm.role = 'researcher';
  userForm.password = '';
  userForm.is_active = true;
}

function openCreateDialog() {
  editingUser.value = null;
  resetUserForm();
  userDialogVisible.value = true;
}

function openEditDialog(user: UserRecord) {
  editingUser.value = user;
  userForm.username = user.username;
  userForm.full_name = user.full_name;
  userForm.role = user.role;
  userForm.password = '';
  userForm.is_active = user.is_active;
  userDialogVisible.value = true;
}

async function submitUserForm() {
  if (!userForm.username || !userForm.full_name) {
    ElMessage.warning('请先填写用户名和姓名');
    return;
  }
  if (!editingUser.value && userForm.password.length < 8) {
    ElMessage.warning('初始密码至少 8 位');
    return;
  }

  userSaving.value = true;
  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, {
        full_name: userForm.full_name,
        role: userForm.role,
        is_active: userForm.is_active,
      });
      ElMessage.success('用户已更新');
    } else {
      await createUser({
        username: userForm.username,
        full_name: userForm.full_name,
        role: userForm.role,
        password: userForm.password,
        is_active: userForm.is_active,
      });
      ElMessage.success('用户已创建');
    }
    userDialogVisible.value = false;
    await loadUsers();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    userSaving.value = false;
  }
}

function openResetPasswordDialog(user: UserRecord) {
  passwordTargetUser.value = user;
  passwordForm.newPassword = '';
  passwordDialogVisible.value = true;
}

async function submitResetPassword() {
  if (!passwordTargetUser.value) {
    return;
  }
  if (passwordForm.newPassword.length < 8) {
    ElMessage.warning('新密码至少 8 位');
    return;
  }

  passwordSaving.value = true;
  try {
    await resetUserPassword(passwordTargetUser.value.id, passwordForm.newPassword);
    ElMessage.success('密码已重置');
    passwordDialogVisible.value = false;
    await loadUsers();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    passwordSaving.value = false;
  }
}

async function handleToggleUserActive(user: UserRecord) {
  try {
    await toggleUserActive(user.id);
    ElMessage.success(`${user.is_active ? '已停用' : '已启用'} ${user.username}`);
    await loadUsers();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  }
}

onMounted(() => {
  void Promise.all([loadConfig(), loadUsers()]);
});
</script>

<style scoped>
.top-gap {
  margin-top: 18px;
}
</style>
