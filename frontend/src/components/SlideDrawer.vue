<script setup>
defineProps({
  side: { type: String, default: 'right', validator: v => ['left', 'right'].includes(v) },
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  sub: { type: String, default: '' }
});
const emit = defineEmits(['close']);
</script>

<template>
  <Transition name="drawer" :class="`drawer-${side}`">
    <div v-if="open" class="drawer-root" :class="`drawer-${side}`">
      <!-- Backdrop scrim -->
      <div class="drawer-backdrop" @click="emit('close')"></div>

      <!-- Panel -->
      <aside class="drawer-panel manuscript-panel" role="dialog" aria-modal="true">
        <header class="drawer-head">
          <div>
            <h2 class="drawer-title label-caps">{{ title }}</h2>
            <p v-if="sub" class="drawer-sub">{{ sub }}</p>
          </div>
          <button class="drawer-close" aria-label="Close drawer" @click="emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="drawer-body">
          <slot />
        </div>
      </aside>
    </div>
  </Transition>
</template>

<style scoped>
.drawer-root {
  position: fixed;
  inset: 0;
  z-index: 80;
}

.drawer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(7, 54, 66, 0.28);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.drawer-panel {
  position: absolute;
  top: 0;
  bottom: 0;
  width: var(--drawer-width);
  max-width: 90vw;
  background: var(--bg-primary);
  border-left: 1px solid rgba(7, 54, 66, 0.25);
  border-right: 1px solid rgba(7, 54, 66, 0.25);
  display: flex;
  flex-direction: column;
  box-shadow: -6px 0 0 0 rgba(7, 54, 66, 0.12);
}

.drawer-right .drawer-panel {
  right: 0;
  box-shadow: -6px 0 0 0 rgba(7, 54, 66, 0.12);
}
.drawer-left .drawer-panel {
  left: 0;
  box-shadow: 6px 0 0 0 rgba(7, 54, 66, 0.12);
}

.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-lg) var(--spacing-md);
  border-bottom: 1px solid rgba(7, 54, 66, 0.12);
}

.drawer-title {
  color: var(--accent-primary);
  font-size: 13px;
}

.drawer-sub {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 4px;
  letter-spacing: 0.05em;
}

.drawer-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  transition: color var(--transition-fast);
}
.drawer-close:hover {
  color: var(--accent-secondary);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}
</style>
