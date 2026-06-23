<script setup>
defineProps({
  sidebarOpen: Boolean,
  rightPanelOpen: Boolean,
  currentPage: String
});

defineEmits(['toggle-sidebar', 'toggle-right-panel', 'update:currentPage']);
</script>

<template>
  <header class="app-header">
    <!-- Left: wordmark + features drawer trigger (chat only) -->
    <div class="header-left">
      <span class="wordmark">AETHER_ARCHIVE</span>
      <div class="divider" v-if="currentPage === 'chat'"></div>
      <button
        v-if="currentPage === 'chat'"
        class="drawer-trigger"
        :class="{ active: sidebarOpen }"
        @click="$emit('toggle-sidebar')"
      >
        <span class="material-symbols-outlined tune-icon">tune</span>
        <span class="trigger-label">CONFIG</span>
      </button>
    </div>

    <!-- Center: nav tabs -->
    <nav class="header-nav">
      <button
        class="nav-tab"
        :class="{ active: currentPage === 'chat' }"
        @click="$emit('update:currentPage', 'chat')"
      >
        <span class="material-symbols-outlined">forum</span>
        <span>RAG Chat</span>
      </button>
      <button
        class="nav-tab"
        :class="{ active: currentPage === 'uploader' }"
        @click="$emit('update:currentPage', 'uploader')"
      >
        <span class="material-symbols-outlined">folder_managed</span>
        <span>Documents</span>
      </button>
    </nav>

    <!-- Right: inspector drawer trigger (chat only) -->
    <div class="header-right">
      <button
        v-if="currentPage === 'chat'"
        class="drawer-trigger"
        :class="{ active: rightPanelOpen }"
        @click="$emit('toggle-right-panel')"
      >
        <span class="trigger-label">INSPECT</span>
        <span class="material-symbols-outlined inspect-icon">vertical_split</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
  padding: 0 var(--spacing-md);
  background: rgba(253, 246, 227, 0.9);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(7, 54, 66, 0.12);
  z-index: 90;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex: 1;
}
.header-right { justify-content: flex-end; }

.wordmark {
  font-family: var(--font-headline);
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -0.01em;
  color: var(--accent-primary);
  white-space: nowrap;
}

.divider {
  width: 1px;
  height: 22px;
  background: rgba(7, 54, 66, 0.15);
}

/* Center nav */
.header-nav {
  display: flex;
  gap: var(--spacing-md);
  flex: 0 0 auto;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 6px 4px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}
.nav-tab .material-symbols-outlined {
  font-size: 18px;
}
.nav-tab:hover { color: var(--text-primary); }
.nav-tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}

/* Drawer triggers */
.drawer-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid rgba(7, 54, 66, 0.2);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 6px 10px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.drawer-trigger .material-symbols-outlined {
  font-size: 18px;
}
.drawer-trigger:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
}
.drawer-trigger.active {
  color: var(--bg-primary);
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}
</style>
