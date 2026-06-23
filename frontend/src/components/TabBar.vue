<script setup>
import { useLayout } from '../composables/useLayout';

const { rightPanelTab } = useLayout();

const tabs = [
  { label: 'Log Stream', value: 0 },
  { label: 'Chunk Inspector', value: 1 },
  { label: 'Comparison', value: 2 }
];
</script>

<template>
  <div class="tab-bar" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      class="tab-btn"
      :class="{ active: rightPanelTab === tab.value }"
      role="tab"
      :aria-selected="(rightPanelTab === tab.value).toString()"
      @click="rightPanelTab = tab.value"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.tab-bar {
  display: flex;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.tab-btn {
  flex-grow: 1;
  background: none;
  border: none;
  padding: 12px var(--spacing-xs);
  color: var(--text-dim);
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: center;
  position: relative;
  user-select: none;
}

.tab-btn:hover {
  color: var(--text-primary);
  background-color: var(--bg-panel-hover);
}

.tab-btn.active {
  color: var(--accent-primary);
  background-color: rgba(0, 240, 255, 0.02);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--accent-primary);
  box-shadow: 0 0 8px var(--accent-primary);
}
</style>
