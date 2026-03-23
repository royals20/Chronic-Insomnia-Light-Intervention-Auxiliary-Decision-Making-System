<template>
  <span class="data-badge" :data-tone="tone" :data-size="size" :data-strong="strong">
    <span v-if="dot" class="data-badge__dot"></span>
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup lang="ts">
import type { BadgeTone } from '@/utils/dataBadges';

withDefaults(
  defineProps<{
    label?: string;
    tone?: BadgeTone;
    size?: 'sm' | 'md';
    strong?: boolean;
    dot?: boolean;
  }>(),
  {
    label: '',
    tone: 'neutral',
    size: 'md',
    strong: false,
    dot: true,
  },
);
</script>

<style scoped>
.data-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.data-badge[data-size='sm'] {
  min-height: 26px;
  padding: 0 10px;
  font-size: 12px;
}

.data-badge[data-strong='true'] {
  font-weight: 700;
}

.data-badge__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.84;
}

.data-badge[data-tone='neutral'] {
  color: #526578;
  background: rgba(82, 101, 120, 0.08);
  border-color: rgba(82, 101, 120, 0.14);
}

.data-badge[data-tone='primary'] {
  color: #0d5f6f;
  background: rgba(13, 95, 111, 0.1);
  border-color: rgba(13, 95, 111, 0.18);
}

.data-badge[data-tone='info'] {
  color: #16567d;
  background: rgba(22, 86, 125, 0.1);
  border-color: rgba(22, 86, 125, 0.18);
}

.data-badge[data-tone='success'] {
  color: #19654b;
  background: rgba(25, 101, 75, 0.1);
  border-color: rgba(25, 101, 75, 0.18);
}

.data-badge[data-tone='warning'] {
  color: #8b5a12;
  background: rgba(139, 90, 18, 0.11);
  border-color: rgba(139, 90, 18, 0.18);
}

.data-badge[data-tone='danger'] {
  color: #9d3644;
  background: rgba(157, 54, 68, 0.1);
  border-color: rgba(157, 54, 68, 0.18);
}
</style>
