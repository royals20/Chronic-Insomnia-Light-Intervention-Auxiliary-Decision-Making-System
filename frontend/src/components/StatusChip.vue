<template>
  <DataBadge :label="label" :tone="badgeTone" size="sm" />
</template>

<script setup lang="ts">
import { computed } from 'vue';

import DataBadge from '@/components/DataBadge.vue';

const props = withDefaults(
  defineProps<{
    label: string;
    tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'primary';
  }>(),
  {
    tone: 'neutral',
  },
);

const badgeTone = computed(() => (props.tone === 'primary' ? 'primary' : props.tone));
</script>
