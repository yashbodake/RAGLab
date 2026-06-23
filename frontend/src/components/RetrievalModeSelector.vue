<script setup>
import { computed } from 'vue';
import { useFeatures } from '../composables/useFeatures';

const { features } = useFeatures();

const selectedMode = computed({
  get() {
    if (features.multi_index) return 'multi-index';
    if (features.hybrid) return 'hybrid';
    return 'dense';
  },
  set(val) {
    if (val === 'dense') {
      features.hybrid = false;
      features.multi_index = false;
    } else if (val === 'hybrid') {
      features.hybrid = true;
      features.multi_index = false;
    } else if (val === 'multi-index') {
      features.multi_index = true;
    }
  }
});
</script>

<template>
  <div class="mode-selector">
    <div class="select-wrapper">
      <select v-model="selectedMode" class="custom-select">
        <option value="dense">Dense Only</option>
        <option value="hybrid">Hybrid</option>
        <option value="multi-index">Multi-Index</option>
      </select>
      <div class="select-arrow">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="var(--text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mode-selector {
  width: 100%;
}

.select-wrapper {
  position: relative;
  width: 100%;
}

.custom-select {
  width: 100%;
  padding: 10px 30px 10px var(--spacing-sm);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.custom-select:hover {
  border-color: rgba(255, 255, 255, 0.2);
}

.custom-select:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.15);
}

.select-arrow {
  position: absolute;
  top: 50%;
  right: var(--spacing-sm);
  transform: translateY(-50%);
  pointer-events: none;
}
</style>
