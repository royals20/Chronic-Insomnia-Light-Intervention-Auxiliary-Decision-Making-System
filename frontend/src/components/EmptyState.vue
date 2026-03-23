<template>
  <div class="empty-state">
    <div class="empty-state__badge">{{ badge }}</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <div v-if="$slots.actions" class="empty-state__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    badge?: string;
    title: string;
    description: string;
  }>(),
  {
    badge: 'STATE',
  },
);
</script>

<style scoped>
.empty-state {
  padding: 36px 24px;
  border-radius: var(--radius-xl);
  border: 1px dashed var(--line-strong);
  background: rgba(250, 252, 255, 0.85);
  text-align: center;
}

.empty-state__badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(13, 95, 111, 0.1);
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.empty-state h3 {
  margin: 18px 0 8px;
  color: var(--ink-strong);
}

.empty-state p {
  margin: 0 auto;
  max-width: 420px;
  color: var(--ink-soft);
  line-height: 1.7;
}

.empty-state__actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}
</style>
