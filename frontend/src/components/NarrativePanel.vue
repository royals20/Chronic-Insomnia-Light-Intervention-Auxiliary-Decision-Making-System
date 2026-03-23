<template>
  <section class="narrative-panel panel-surface" :data-tone="tone">
    <header class="narrative-panel__header">
      <div class="narrative-panel__copy">
        <span v-if="eyebrow" class="narrative-panel__eyebrow">{{ eyebrow }}</span>
        <h2>{{ title }}</h2>
        <p v-if="description">{{ description }}</p>
      </div>

      <div v-if="$slots.actions" class="narrative-panel__actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="narrative-panel__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="narrative-panel__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    description?: string;
    eyebrow?: string;
    tone?: 'default' | 'accent' | 'warning';
  }>(),
  {
    tone: 'default',
  },
);
</script>

<style scoped>
.narrative-panel {
  padding: 24px;
}

.narrative-panel[data-tone='accent'] {
  background:
    radial-gradient(circle at top right, rgba(13, 95, 111, 0.1), transparent 28%),
    var(--surface-card);
}

.narrative-panel[data-tone='warning'] {
  background:
    radial-gradient(circle at top right, rgba(139, 90, 18, 0.1), transparent 28%),
    var(--surface-card);
}

.narrative-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.narrative-panel__copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.narrative-panel__eyebrow {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.narrative-panel h2 {
  margin: 0;
  color: var(--ink-strong);
  font-size: 24px;
  line-height: 1.15;
}

.narrative-panel p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.narrative-panel__actions,
.narrative-panel__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.narrative-panel__body {
  margin-top: 18px;
}

.narrative-panel__footer {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--line-soft);
}

@media (max-width: 960px) {
  .narrative-panel {
    padding: 20px;
  }

  .narrative-panel__header {
    flex-direction: column;
  }
}
</style>
