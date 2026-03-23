<template>
  <nav class="section-nav-rail panel-surface" aria-label="页面章节导航">
    <button
      v-for="item in sections"
      :key="item.id"
      type="button"
      class="section-nav-rail__item"
      :class="{ 'is-active': item.id === activeId }"
      @click="$emit('navigate', item.id)"
    >
      <strong>{{ item.label }}</strong>
      <span v-if="item.caption">{{ item.caption }}</span>
    </button>
  </nav>
</template>

<script setup lang="ts">
export interface SectionNavItem {
  id: string;
  label: string;
  caption?: string;
}

defineProps<{
  sections: SectionNavItem[];
  activeId: string;
}>();

defineEmits<{
  navigate: [id: string];
}>();
</script>

<style scoped>
.section-nav-rail {
  position: sticky;
  top: 88px;
  z-index: 4;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px;
}

.section-nav-rail__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: transparent;
  color: var(--ink-soft);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
}

.section-nav-rail__item strong {
  color: inherit;
  font-size: 14px;
}

.section-nav-rail__item span {
  font-size: 12px;
  color: var(--ink-muted);
}

.section-nav-rail__item:hover,
.section-nav-rail__item.is-active {
  transform: translateY(-1px);
  color: var(--ink-strong);
  background: rgba(13, 95, 111, 0.08);
  border-color: rgba(13, 95, 111, 0.14);
}

.section-nav-rail__item.is-active span {
  color: var(--accent-strong);
}

@media (max-width: 960px) {
  .section-nav-rail {
    position: static;
  }

  .section-nav-rail__item {
    min-width: calc(50% - 5px);
  }
}
</style>
