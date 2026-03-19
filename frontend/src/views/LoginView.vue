<template>
  <div class="login-page">
    <div class="login-intro">
      <span class="intro-badge">科研原型</span>
      <h1>慢性失眠光干预科研辅助决策系统</h1>
      <p>
        当前版本用于论文展示、科研演示与软著申请，聚焦原型流程与界面框架，不承载真实临床诊疗。
      </p>
      <el-alert
        title="仅供科研辅助，不替代临床诊断与治疗"
        type="warning"
        :closable="false"
        show-icon
      />
    </div>

    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-card__header">
          <div>
            <h2>系统登录</h2>
            <p>请输入演示账号进入原型系统</p>
          </div>
        </div>
      </template>

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
          登录系统
        </el-button>
      </el-form>

      <div class="demo-account">
        <p>演示账号：research_demo</p>
        <p>演示密码：Demo@123456</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRoute, useRouter } from 'vue-router';

import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);

const form = reactive({
  username: 'research_demo',
  password: 'Demo@123456',
});

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码');
    return;
  }

  loading.value = true;
  try {
    const response = await authStore.login(form);
    ElMessage.success(response.message);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard';
    router.push(redirect);
  } catch (error) {
    ElMessage.error('登录失败，请检查演示账号信息');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(320px, 1.15fr) minmax(320px, 420px);
  background:
    radial-gradient(circle at top left, rgba(34, 140, 121, 0.2), transparent 32%),
    linear-gradient(135deg, #eef5fb 0%, #f7fbff 45%, #f2f5f8 100%);
}

.login-intro {
  padding: 72px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 20px;
}

.intro-badge {
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: #0f5d73;
  color: #fff;
  font-size: 13px;
}

.login-intro h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.25;
  color: #11385e;
}

.login-intro p {
  margin: 0;
  max-width: 520px;
  color: #5d7084;
  font-size: 16px;
  line-height: 1.8;
}

.login-card {
  margin: auto 48px auto 0;
  width: min(100%, 420px);
  border-radius: 20px;
}

.login-card__header h2 {
  margin: 0 0 8px;
  color: #173654;
}

.login-card__header p {
  margin: 0;
  color: #718194;
}

.submit-button {
  width: 100%;
  margin-top: 8px;
}

.demo-account {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed #d8e1ea;
  color: #607487;
  font-size: 13px;
  line-height: 1.8;
}

.demo-account p {
  margin: 0;
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-intro {
    padding: 40px 24px 16px;
  }

  .login-intro h1 {
    font-size: 30px;
  }

  .login-card {
    margin: 0 24px 32px;
    width: auto;
  }
}
</style>
