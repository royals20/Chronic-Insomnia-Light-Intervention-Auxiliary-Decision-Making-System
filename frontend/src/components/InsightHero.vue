<template>
  <section class="insight-hero panel-surface" :class="{ 'has-aside': !!$slots.aside }">
    <div class="insight-hero__main">
      <span v-if="eyebrow" class="insight-hero__eyebrow">{{ eyebrow }}</span>
      <h1>{{ title }}</h1>
      <p v-if="description" class="insight-hero__description">{{ description }}</p>

      <div v-if="$slots.meta" class="insight-hero__meta">
        <slot name="meta" />
      </div>

      <div v-if="$slots.actions" class="insight-hero__actions">
        <slot name="actions" />
      </div>
    </div>

    <aside v-if="$slots.aside" class="insight-hero__aside">
      <slot name="aside" />
    </aside>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
  eyebrow?: string;
}>();
</script>

<style scoped>
.insight-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr);
  gap: 26px;
  padding: 32px;
  overflow: hidden;
  position: relative;
}

.insight-hero::before {
  content: '';
  position: absolute;
  inset: 0 0 auto auto;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(13, 95, 111, 0.12), transparent 68%);
  pointer-events: none;
}

.insight-hero.has-aside {
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.8fr);
}

.insight-hero__main,
.insight-hero__aside {
  position: relative;
  z-index: 1;
}

.insight-hero__main {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.insight-hero__eyebrow {
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(13, 95, 111, 0.1);
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.insight-hero h1 {
  margin: 0;
  max-width: 900px;
  color: var(--ink-strong);
  font-size: clamp(34px, 3.4vw, 52px);
  line-height: 1.02;
  letter-spacing: -0.03em;
}

.insight-hero__description {
  margin: 0;
  max-width: 860px;
  color: var(--ink-soft);
  font-size: 16px;
  line-height: 1.8;
}

.insight-hero__meta,
.insight-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.insight-hero__actions {
  padding-top: 4px;
}

.insight-hero__aside {
  align-self: stretch;
}

@media (max-width: 1100px) {
  .insight-hero,
  .insight-hero.has-aside {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .insight-hero {
    padding: 24px;
  }

  .insight-hero h1 {
    font-size: clamp(30px, 8vw, 42px);
  }
}
</style>
