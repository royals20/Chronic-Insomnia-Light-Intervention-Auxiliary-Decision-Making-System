<template>
  <div class="forbidden-page">
    <ForbiddenState />
  </div>
</template>

<script setup lang="ts">
import ForbiddenState from '@/components/ForbiddenState.vue';
</script>

<style scoped>
.forbidden-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
