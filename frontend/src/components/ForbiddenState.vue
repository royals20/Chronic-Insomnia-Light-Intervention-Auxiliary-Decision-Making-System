<template>
  <EmptyState
    badge="403"
    title="当前账号没有访问此页面的权限"
    description="权限以后端角色为准。你可以返回仪表盘，或使用拥有更高权限的账号重新登录。"
  >
    <template #actions>
      <el-button type="primary" @click="$router.push('/dashboard')">返回总览</el-button>
      <el-button plain @click="$router.push('/login')">重新登录</el-button>
    </template>
  </EmptyState>
</template>

<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue';
</script>
