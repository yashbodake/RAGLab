<script setup>
import FeatureToggles from './FeatureToggles.vue';
import RetrievalModeSelector from './RetrievalModeSelector.vue';
import MetricsPanel from './MetricsPanel.vue';

// When embedded (rendered inside SlideDrawer), the outer chrome is dropped —
// the drawer supplies width, scrolling, and the manuscript panel surface.
defineProps({
  open: { type: Boolean, default: true },
  embedded: { type: Boolean, default: false }
});
</script>

<template>
  <div class="left-sidebar-content">
    <section class="sidebar-section">
      <h3 class="section-title label-caps">Retrieval Config</h3>
      <RetrievalModeSelector />
    </section>

    <section class="sidebar-section">
      <h3 class="section-title label-caps">Advanced Features</h3>
      <FeatureToggles />
    </section>

    <section class="sidebar-section">
      <h3 class="section-title label-caps">Performance Metrics</h3>
      <MetricsPanel />
    </section>
  </div>
</template>

<style scoped>
.left-sidebar-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  color: var(--accent-secondary);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid rgba(7, 54, 66, 0.12);
}
</style>
