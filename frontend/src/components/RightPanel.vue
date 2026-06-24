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
      <Transition name="tab-swap" mode="out-in">
        <LogStreamTab v-if="rightPanelTab === 0" key="logs" />
        <ChunkInspectorTab v-else-if="rightPanelTab === 1" key="chunks" />
        <ComparisonTab v-else key="compare" />
      </Transition>
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

/* Quick cross-fade when switching inspector tabs */
.tab-swap-enter-active,
.tab-swap-leave-active {
  transition: opacity 0.18s ease;
}
.tab-swap-enter-from,
.tab-swap-leave-to {
  opacity: 0;
}
</style>
