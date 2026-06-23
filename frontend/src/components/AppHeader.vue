<script setup>
defineProps({
  sidebarOpen: Boolean,
  rightPanelOpen: Boolean,
  currentPage: String
});

defineEmits(['toggle-sidebar', 'toggle-right-panel', 'update:currentPage']);
</script>

<template>
  <header class="app-header glass-panel">
    <div class="header-left">
      <!-- Hamburger Menu Button -->
      <button 
        v-if="currentPage === 'chat'"
        class="icon-button" 
        :class="{ active: sidebarOpen }"
        aria-label="Toggle Features Sidebar"
        @click="$emit('toggle-sidebar')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="12" x2="20" y2="12"></line>
          <line x1="4" y1="6" x2="20" y2="6"></line>
          <line x1="4" y1="18" x2="20" y2="18"></line>
        </svg>
      </button>

      <!-- App Logo -->
      <div class="logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="var(--accent-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
        </svg>
        <span class="logo-text">Industrial RAG <span class="accent-text">Demonstrator</span></span>
      </div>
    </div>

    <!-- Centered Nav Tabs -->
    <div class="header-nav">
      <button 
        class="nav-tab" 
        :class="{ active: currentPage === 'chat' }"
        @click="$emit('update:currentPage', 'chat')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span>RAG Chat</span>
      </button>
      <button 
        class="nav-tab" 
        :class="{ active: currentPage === 'uploader' }"
        @click="$emit('update:currentPage', 'uploader')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <polyline points="9 15 12 12 15 15"></polyline>
        </svg>
        <span>Document Manager</span>
      </button>
    </div>

    <!-- Right Drawer Toggle -->
    <div class="header-right" v-if="currentPage === 'chat'">
      <button 
        class="icon-button" 
        :class="{ active: rightPanelOpen }"
        aria-label="Toggle Inspect Drawer"
        @click="$emit('toggle-right-panel')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="9" y1="3" x2="9" y2="21"></line>
        </svg>
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
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  background-color: rgba(11, 15, 25, 0.7);
  z-index: 10;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-text {
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: 0.5px;
}

.accent-text {
  color: var(--accent-primary);
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
}

.header-nav {
  display: flex;
  gap: var(--spacing-xs);
  background-color: rgba(17, 24, 39, 0.5);
  padding: 3px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-tab:hover {
  color: var(--text-primary);
  background-color: rgba(255, 255, 255, 0.02);
}

.nav-tab.active {
  color: var(--accent-primary);
  background-color: var(--bg-primary);
  border-color: var(--border-subtle);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.1);
}

.nav-icon {
  transition: color var(--transition-fast);
  color: var(--text-muted);
}

.nav-tab.active .nav-icon {
  color: var(--accent-primary);
}

.icon-button {
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.icon-button:hover {
  color: var(--text-primary);
  background-color: var(--bg-panel-hover);
  border-color: var(--border-subtle);
}

.icon-button.active {
  color: var(--accent-primary);
  border-color: var(--border-active);
  background-color: rgba(0, 240, 255, 0.05);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.15);
}
</style>
