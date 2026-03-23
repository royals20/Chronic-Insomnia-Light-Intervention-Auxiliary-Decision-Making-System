<template>
  <div class="page-header">
    <div class="page-header__copy">
      <span v-if="eyebrow" class="page-header__eyebrow">{{ eyebrow }}</span>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
      <div v-if="$slots.meta" class="page-header__meta">
        <slot name="meta" />
      </div>
    </div>

    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
  eyebrow?: string;
}>();
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.page-header__copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-header__eyebrow {
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(13, 95, 111, 0.12);
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-header h1 {
  margin: 0;
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.05;
  color: var(--ink-strong);
}

.page-header p {
  margin: 0;
  max-width: 720px;
  color: var(--ink-soft);
  line-height: 1.7;
}

.page-header__meta,
.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
