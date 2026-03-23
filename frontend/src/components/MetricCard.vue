<template>
  <div class="metric-card" :data-tone="tone">
    <span class="metric-card__label">{{ label }}</span>
    <strong class="metric-card__value">{{ value }}</strong>
    <p v-if="description" class="metric-card__description">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    value: string | number;
    description?: string;
    tone?: 'sky' | 'teal' | 'sand';
  }>(),
  {
    tone: 'sky',
  },
);
</script>

<style scoped>
.metric-card {
  padding: 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.98));
}

.metric-card[data-tone='teal'] {
  background: linear-gradient(180deg, rgba(244, 252, 251, 0.96), rgba(234, 247, 245, 1));
}

.metric-card[data-tone='sand'] {
  background: linear-gradient(180deg, rgba(255, 250, 243, 0.96), rgba(252, 244, 231, 1));
}

.metric-card__label {
  color: var(--ink-muted);
  font-size: 13px;
}

.metric-card__value {
  display: block;
  margin-top: 14px;
  color: var(--ink-strong);
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1;
}

.metric-card__description {
  margin: 12px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}
</style>
