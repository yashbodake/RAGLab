<script setup>
import { useLayout } from '../composables/useLayout';
import TabBar from './TabBar.vue';
import LogStreamTab from './LogStreamTab.vue';
import ChunkInspectorTab from './ChunkInspectorTab.vue';
import ComparisonTab from './ComparisonTab.vue';

defineProps({
  open: { type: Boolean, default: true },
  embedded: { type: Boolean, default: false }
});

const { rightPanelTab } = useLayout();
</script>

<template>
  <div class="right-panel-content">
    <TabBar />
    <div class="panel-content">
      <LogStreamTab v-if="rightPanelTab === 0" />
      <ChunkInspectorTab v-if="rightPanelTab === 1" />
      <ComparisonTab v-if="rightPanelTab === 2" />
    </div>
  </div>
</template>

<style scoped>
.right-panel-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.panel-content {
  display: flex;
  flex-direction: column;
}
</style>
