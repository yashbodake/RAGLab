<script setup>
import FeatureToggles from './FeatureToggles.vue';
import RetrievalModeSelector from './RetrievalModeSelector.vue';
import MetricsPanel from './MetricsPanel.vue';

defineProps({
  open: Boolean
});
</script>

<template>
  <aside class="left-sidebar glass-panel" :class="{ collapsed: !open }">
    <div class="sidebar-scroll">
      <div class="sidebar-section">
        <h3>Retrieval Config</h3>
        <RetrievalModeSelector />
      </div>

      <div class="sidebar-section">
        <h3>Advanced Features</h3>
        <FeatureToggles />
      </div>

      <div class="sidebar-section">
        <h3>Performance Metrics</h3>
        <MetricsPanel />
      </div>
    </div>
  </aside>
</template>

<style scoped>
.left-sidebar {
  width: var(--sidebar-width);
  height: 100%;
  border-radius: 0;
  border-top: none;
  border-bottom: none;
  border-left: none;
  background-color: rgba(17, 24, 39, 0.45);
  transition: transform var(--transition-normal), width var(--transition-normal);
  flex-shrink: 0;
  overflow: hidden;
  z-index: 5;
}

.left-sidebar.collapsed {
  width: 0;
  transform: translateX(-100%);
  border-right: none;
}

.sidebar-scroll {
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.sidebar-section h3 {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-dim);
  margin-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: var(--spacing-xs);
}
</style>
