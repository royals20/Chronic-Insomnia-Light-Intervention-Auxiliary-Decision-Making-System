<template>
  <el-card shadow="never" class="section-card">
    <template #header>
      <div class="section-card__header">
        <div>
          <div class="section-card__title">{{ title }}</div>
          <p v-if="description" class="section-card__description">{{ description }}</p>
        </div>
        <div v-if="$slots.actions" class="section-card__actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <slot />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<style scoped>
.section-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: var(--surface-card);
  box-shadow: var(--shadow-card);
}

.section-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.section-card__title {
  color: var(--ink-strong);
  font-size: 18px;
  font-weight: 700;
}

.section-card__description {
  margin: 6px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.section-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .section-card__header {
    flex-direction: column;
  }
}
</style>
