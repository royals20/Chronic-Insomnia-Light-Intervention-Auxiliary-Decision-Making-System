<template>
  <div class="insight-summary-strip panel-surface">
    <article
      v-for="item in items"
      :key="item.label"
      class="insight-summary-strip__item"
      :data-tone="item.tone || 'neutral'"
    >
      <span class="insight-summary-strip__label">{{ item.label }}</span>
      <strong class="insight-summary-strip__value">{{ item.value }}</strong>
      <p v-if="item.description" class="insight-summary-strip__description">{{ item.description }}</p>
    </article>
  </div>
</template>

<script setup lang="ts">
import type { BadgeTone } from '@/utils/dataBadges';

export interface InsightSummaryItem {
  label: string;
  value: string | number;
  description?: string;
  tone?: BadgeTone;
}

defineProps<{
  items: InsightSummaryItem[];
}>();
</script>

<style scoped>
.insight-summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0;
  overflow: hidden;
}

.insight-summary-strip__item {
  padding: 22px 24px;
  border-right: 1px solid var(--line-soft);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.28));
}

.insight-summary-strip__item:last-child {
  border-right: 0;
}

.insight-summary-strip__item[data-tone='primary'] {
  background: linear-gradient(180deg, rgba(13, 95, 111, 0.1), rgba(13, 95, 111, 0.03));
}

.insight-summary-strip__item[data-tone='success'] {
  background: linear-gradient(180deg, rgba(25, 101, 75, 0.1), rgba(25, 101, 75, 0.03));
}

.insight-summary-strip__item[data-tone='warning'] {
  background: linear-gradient(180deg, rgba(139, 90, 18, 0.1), rgba(139, 90, 18, 0.03));
}

.insight-summary-strip__item[data-tone='danger'] {
  background: linear-gradient(180deg, rgba(157, 54, 68, 0.1), rgba(157, 54, 68, 0.03));
}

.insight-summary-strip__label {
  display: block;
  color: var(--ink-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.insight-summary-strip__value {
  display: block;
  margin-top: 14px;
  color: var(--ink-strong);
  font-size: clamp(28px, 2.8vw, 38px);
  line-height: 1;
}

.insight-summary-strip__description {
  margin: 10px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

@media (max-width: 960px) {
  .insight-summary-strip__item {
    border-right: 0;
    border-bottom: 1px solid var(--line-soft);
  }

  .insight-summary-strip__item:last-child {
    border-bottom: 0;
  }
}
</style>
