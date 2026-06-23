<script setup>
import { ref } from 'vue';
import SourceChip from './SourceChip.vue';

defineProps({
  sources: Array
});

const expanded = ref(false);
</script>

<template>
  <div class="sources-accordion">
    <button class="accordion-toggle" @click="expanded = !expanded">
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 24 24" 
        width="14" 
        height="14" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2.5" 
        stroke-linecap="round" 
        stroke-linejoin="round"
        class="toggle-arrow"
        :class="{ rotated: expanded }"
      >
        <polyline points="9 18 15 12 9 6"></polyline>
      </svg>
      <span>Cited Sources ({{ sources.length }})</span>
    </button>
    
    <div v-show="expanded" class="accordion-content">
      <div class="chips-container">
        <SourceChip v-for="src in sources" :key="src.id" :chunk="src" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.sources-accordion {
  margin-top: var(--spacing-xs);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.accordion-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  background: none;
  border: none;
  color: var(--text-dim);
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  padding: var(--spacing-xs) 0;
  user-select: none;
  transition: color var(--transition-fast);
}

.accordion-toggle:hover {
  color: var(--text-primary);
}

.toggle-arrow {
  transition: transform var(--transition-fast);
}

.toggle-arrow.rotated {
  transform: rotate(90deg);
}

.accordion-content {
  margin-top: var(--spacing-xs);
  width: 100%;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}
</style>
