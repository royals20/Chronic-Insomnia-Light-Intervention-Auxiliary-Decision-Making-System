<template>
  <div class="page-stack">
    <DisclaimerBanner />

    <PageHeader
      eyebrow="Subjects"
      title="受试者工作台"
      description="围绕档案、录入进度和关键状态组织受试者视图。研究员仅可查看详情，管理员和录入员可继续录入。"
    >
      <template #meta>
        <StatusChip :label="canEditPatient ? '可编辑' : '只读模式'" :tone="canEditPatient ? 'success' : 'warning'" />
      </template>
      <template #actions>
        <ToolbarRow>
          <el-button v-if="canCreatePatient" type="primary" plain @click="openCreateDialog">新增受试者</el-button>
          <el-button @click="handleSearch">刷新列表</el-button>
        </ToolbarRow>
      </template>
    </PageHeader>

    <SectionCard title="筛选与查询" description="按编号、性别和录入完成度快速定位受试者。">
      <ToolbarRow>
        <el-input
          v-model="keyword"
          placeholder="按受试者编号或匿名编号搜索"
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />

        <el-select v-model="gender" clearable placeholder="性别筛选" class="filter-item">
          <el-option label="男" value="男" />
          <el-option label="女" value="女" />
        </el-select>

        <el-select v-model="followupFilter" placeholder="随访状态" class="filter-item">
          <el-option label="全部随访状态" value="all" />
          <el-option label="已录入随访" value="true" />
          <el-option label="未录入随访" value="false" />
        </el-select>

        <el-select v-model="interventionFilter" placeholder="干预状态" class="filter-item">
          <el-option label="全部干预状态" value="all" />
          <el-option label="已录入干预" value="true" />
          <el-option label="未录入干预" value="false" />
        </el-select>

        <el-button type="primary" plain @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </ToolbarRow>
    </SectionCard>

    <SectionCard title="受试者列表" description="表格右侧操作会按角色自动裁剪。">
      <el-table v-loading="loading" :data="patients" stripe>
        <el-table-column prop="patient_code" label="受试者编号" min-width="130" />
        <el-table-column prop="anonymized_code" label="匿名编号" min-width="130" />
        <el-table-column prop="gender" label="性别" width="90" />
        <el-table-column prop="age" label="年龄" width="90" />
        <el-table-column prop="education_level" label="教育程度" min-width="110" />
        <el-table-column label="基线" width="100">
          <template #default="{ row }">
            <StatusChip :label="row.has_baseline_feature ? '已录入' : '待录入'" :tone="row.has_baseline_feature ? 'success' : 'neutral'" />
          </template>
        </el-table-column>
        <el-table-column label="干预" width="100">
          <template #default="{ row }">
            <StatusChip :label="row.has_light_intervention ? '已录入' : '待录入'" :tone="row.has_light_intervention ? 'success' : 'neutral'" />
          </template>
        </el-table-column>
        <el-table-column label="随访" width="100">
          <template #default="{ row }">
            <StatusChip :label="row.has_followup_outcome ? '已录入' : '待录入'" :tone="row.has_followup_outcome ? 'success' : 'warning'" />
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="260" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button text type="primary" @click="goToDetail(row.id)">详情</el-button>
              <el-button
                v-if="canEditPatient"
                text
                type="primary"
                @click="goToSection(row.id, 'baseline')"
              >
                基线
              </el-button>
              <el-button
                v-if="canEditPatient"
                text
                type="primary"
                @click="goToSection(row.id, 'questionnaire')"
              >
                量表
              </el-button>
              <el-button
                v-if="canEditPatient"
                text
                type="primary"
                @click="goToSection(row.id, 'light')"
              >
                干预
              </el-button>
              <el-button
                v-if="canEditPatient"
                text
                type="primary"
                @click="goToSection(row.id, 'followup')"
              >
                随访
              </el-button>
            </div>
          </template>
        </el-table-column>
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

    <el-dialog v-model="createDialogVisible" title="新增受试者" width="720px">
      <el-form ref="formRef" :model="createForm" :rules="rules" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="受试者编号" prop="patient_code">
              <el-input v-model="createForm.patient_code" placeholder="例如 PAT-202603-001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="匿名编号" prop="anonymized_code">
              <el-input v-model="createForm.anonymized_code" placeholder="例如 ANON-001" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="createForm.gender" placeholder="请选择性别" class="full-width">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年龄" prop="age">
              <el-input-number v-model="createForm.age" :min="0" :max="120" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="教育程度" prop="education_level">
              <el-select v-model="createForm.education_level" placeholder="请选择教育程度" class="full-width">
                <el-option label="高中" value="高中" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身高(cm)" prop="height_cm">
              <el-input-number v-model="createForm.height_cm" :min="0" :max="300" :precision="1" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="体重(kg)" prop="weight_kg">
              <el-input-number v-model="createForm.weight_kg" :min="0" :max="500" :precision="1" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="remarks">
              <el-input v-model="createForm.remarks" type="textarea" :rows="3" placeholder="可填写来源或录入说明" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">保存并查看详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import DisclaimerBanner from '@/components/DisclaimerBanner.vue';
import PageHeader from '@/components/PageHeader.vue';
import SectionCard from '@/components/SectionCard.vue';
import StatusChip from '@/components/StatusChip.vue';
import ToolbarRow from '@/components/ToolbarRow.vue';
import { createPatient, fetchPatients, type PatientCreatePayload, type PatientListItem } from '@/api/subjects';
import { useAuthStore } from '@/stores/auth';
import { formatDateTime } from '@/utils/format';

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const creating = ref(false);
const patients = ref<PatientListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const keyword = ref('');
const gender = ref<string | undefined>();
const followupFilter = ref<'all' | 'true' | 'false'>('all');
const interventionFilter = ref<'all' | 'true' | 'false'>('all');
const createDialogVisible = ref(false);
const formRef = ref<FormInstance>();

const canCreatePatient = computed(() => authStore.can('create_patient'));
const canEditPatient = computed(() => authStore.can('edit_patient'));

const createForm = reactive<PatientCreatePayload>({
  patient_code: '',
  anonymized_code: '',
  gender: null,
  age: null,
  height_cm: null,
  weight_kg: null,
  education_level: null,
  remarks: null,
});

const rules: FormRules<PatientCreatePayload> = {
  patient_code: [{ required: true, message: '请输入受试者编号', trigger: 'blur' }],
  anonymized_code: [{ required: true, message: '请输入匿名编号', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'change' }],
};

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return '操作失败，请稍后重试';
}

function parseBooleanFilter(value: 'all' | 'true' | 'false') {
  if (value === 'all') {
    return undefined;
  }
  return value === 'true';
}

async function loadPatients() {
  loading.value = true;
  try {
    const data = await fetchPatients({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value || undefined,
      gender: gender.value,
      has_followup_outcome: parseBooleanFilter(followupFilter.value),
      has_light_intervention: parseBooleanFilter(interventionFilter.value),
    });
    patients.value = data.items;
    total.value = data.total;
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  page.value = 1;
  void loadPatients();
}

function handleReset() {
  keyword.value = '';
  gender.value = undefined;
  followupFilter.value = 'all';
  interventionFilter.value = 'all';
  handleSearch();
}

function handlePageChange(nextPage: number) {
  page.value = nextPage;
  void loadPatients();
}

function openCreateDialog() {
  if (!canCreatePatient.value) {
    return;
  }
  createDialogVisible.value = true;
}

function resetCreateForm() {
  createForm.patient_code = '';
  createForm.anonymized_code = '';
  createForm.gender = null;
  createForm.age = null;
  createForm.height_cm = null;
  createForm.weight_kg = null;
  createForm.education_level = null;
  createForm.remarks = null;
}

async function handleCreate() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  creating.value = true;
  try {
    const patient = await createPatient(createForm);
    ElMessage.success('受试者创建成功');
    createDialogVisible.value = false;
    resetCreateForm();
    await loadPatients();
    await router.push(`/subjects/${patient.id}`);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    creating.value = false;
  }
}

function goToDetail(patientId: number) {
  void router.push(`/subjects/${patientId}`);
}

function goToSection(patientId: number, section: string) {
  void router.push(`/subjects/${patientId}/${section}`);
}

onMounted(() => {
  void loadPatients();
});
</script>

<style scoped>
.search-input {
  width: min(320px, 100%);
}

.filter-item {
  width: 180px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 960px) {
  .search-input,
  .filter-item {
    width: 100%;
  }
}
</style>
