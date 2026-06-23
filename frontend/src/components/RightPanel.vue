<script setup>
import { useLayout } from '../composables/useLayout';
import TabBar from './TabBar.vue';
import LogStreamTab from './LogStreamTab.vue';
import ChunkInspectorTab from './ChunkInspectorTab.vue';
import ComparisonTab from './ComparisonTab.vue';

defineProps({
  open: Boolean
});

const { rightPanelTab } = useLayout();
</script>

<template>
  <aside class="right-panel glass-panel" :class="{ collapsed: !open }">
    <TabBar />
    <div class="panel-content">
      <LogStreamTab v-if="rightPanelTab === 0" />
      <ChunkInspectorTab v-if="rightPanelTab === 1" />
      <ComparisonTab v-if="rightPanelTab === 2" />
    </div>
  </aside>
</template>

<style scoped>
.right-panel {
  width: var(--right-panel-width);
  height: 100%;
  border-radius: 0;
  border-top: none;
  border-bottom: none;
  border-right: none;
  background-color: rgba(17, 24, 39, 0.45);
  transition: transform var(--transition-normal), width var(--transition-normal);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 5;
}

.right-panel.collapsed {
  width: 0;
  transform: translateX(100%);
  border-left: none;
}

.panel-content {
  flex-grow: 1;
  overflow: hidden;
}
</style>
