<template>
  <div class="toolbar-row">
    <slot />
  </div>
</template>

<style scoped>
.toolbar-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
</style>
