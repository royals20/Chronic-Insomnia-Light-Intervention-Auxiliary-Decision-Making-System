<template>
  <div class="login-page">
    <section class="login-hero">
      <InsightHero
        eyebrow="Phase II Upgrade"
        title="科研辅助决策平台已切换到驾驶舱式访问模式"
        description="本轮升级强调角色化访问、统一设计系统和分析结果可解释展示。登录后会按管理员、研究员、录入员装配不同入口与权限边界。"
      >
        <template #meta>
          <DataBadge label="仅供科研辅助" tone="warning" />
          <DataBadge label="JWT 鉴权" tone="primary" />
          <DataBadge label="RBAC 已启用" tone="success" />
        </template>
      </InsightHero>

      <div class="account-grid">
        <button type="button" class="account-card" @click="fillDemo('admin_demo', 'Admin@123456')">
          <span>管理员</span>
          <strong>admin_demo</strong>
          <p>用户管理、系统配置、数据治理和模型演示全权限。</p>
        </button>
        <button type="button" class="account-card" @click="fillDemo('research_demo', 'Demo@123456')">
          <span>研究员</span>
          <strong>research_demo</strong>
          <p>只读查看数据，可评估、报告、训练并解释因果结果。</p>
        </button>
        <button type="button" class="account-card" @click="fillDemo('data_entry_demo', 'Entry@123456')">
          <span>录入员</span>
          <strong>data_entry_demo</strong>
          <p>聚焦导入与录入，不可访问推荐、报告和模型中心。</p>
        </button>
      </div>

      <InsightSummaryStrip :items="loginSummaryItems" />
    </section>

    <section class="login-panel panel-surface">
      <div class="login-panel__header">
        <span>Access Control</span>
        <h2>登录系统</h2>
        <p>输入账号密码后，前端会根据后端返回的角色动态装配导航与操作权限。</p>
      </div>

      <el-form :model="form" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
        </el-form-item>

        <el-button type="primary" class="submit-button" :loading="loading" @click="handleLogin">
          登录并加载角色权限
        </el-button>
      </el-form>

      <div class="credentials-block">
        <div>
          <span>当前账号</span>
          <strong>{{ form.username || '--' }}</strong>
        </div>
        <div>
          <span>状态</span>
          <strong>{{ loading ? '验证中' : '待登录' }}</strong>
        </div>
      </div>

      <div class="login-note">
        <strong>科研声明</strong>
        <p>本系统仅用于科研演示、论文展示和辅助决策流程验证，不替代临床诊断与治疗。</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRoute, useRouter } from 'vue-router';

import DataBadge from '@/components/DataBadge.vue';
import InsightHero from '@/components/InsightHero.vue';
import InsightSummaryStrip from '@/components/InsightSummaryStrip.vue';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);

const form = reactive({
  username: 'research_demo',
  password: 'Demo@123456',
});

const loginSummaryItems = computed(() => [
  { label: '默认演示账号', value: '3 个', description: '管理员、研究员、录入员三角色。', tone: 'primary' as const },
  { label: '鉴权方式', value: 'JWT', description: '登录后按角色装配导航与按钮。', tone: 'success' as const },
  { label: '页面目标', value: '答辩展示', description: '围绕科研链路与决策解释展开。', tone: 'warning' as const },
]);

function fillDemo(username: string, password: string) {
  form.username = username;
  form.password = password;
}

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码');
    return;
  }

  loading.value = true;
  try {
    const response = await authStore.login(form);
    ElMessage.success(`${response.message}，当前角色：${response.user.role}`);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard';
    await router.push(redirect);
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '登录失败，请检查账号信息');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 440px);
  gap: 0;
}

.login-hero {
  padding: 40px 36px 36px 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 22px;
  background:
    radial-gradient(circle at top left, rgba(15, 95, 111, 0.16), transparent 30%),
    radial-gradient(circle at bottom right, rgba(155, 108, 47, 0.12), transparent 22%);
}

.account-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}

.account-card {
  padding: 22px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-soft);
  text-align: left;
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-base), border-color var(--transition-base);
}

.account-card:hover {
  transform: translateY(-2px);
  border-color: rgba(13, 95, 111, 0.18);
  box-shadow: var(--shadow-card);
}

.account-card span {
  color: var(--accent-strong);
  font-size: 13px;
  font-weight: 700;
}

.account-card strong {
  display: block;
  margin: 10px 0 12px;
  color: var(--ink-strong);
  font-size: 21px;
}

.account-card p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.login-panel {
  margin: 36px 36px 36px 0;
  align-self: center;
  padding: 28px;
}

.login-panel__header span {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-panel__header h2 {
  margin: 10px 0 8px;
  color: var(--ink-strong);
  font-size: 32px;
}

.login-panel__header p {
  margin: 0 0 20px;
  color: var(--ink-soft);
  line-height: 1.7;
}

.submit-button {
  width: 100%;
  margin-top: 10px;
}

.credentials-block {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
}

.credentials-block > div {
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--surface-soft);
  border: 1px solid var(--line-soft);
}

.credentials-block span {
  display: block;
  color: var(--ink-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.credentials-block strong {
  display: block;
  margin-top: 10px;
  color: var(--ink-strong);
}

.login-note {
  margin-top: 20px;
  padding: 18px 20px;
  border-radius: var(--radius-lg);
  background: rgba(13, 95, 111, 0.06);
  border: 1px solid rgba(13, 95, 111, 0.12);
}

.login-note strong {
  color: var(--ink-strong);
}

.login-note p {
  margin: 10px 0 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

@media (max-width: 1120px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-panel {
    margin: 0 24px 32px;
  }
}

@media (max-width: 960px) {
  .login-hero {
    padding: 24px 20px 18px;
  }

  .credentials-block {
    grid-template-columns: 1fr;
  }
}
</style>
