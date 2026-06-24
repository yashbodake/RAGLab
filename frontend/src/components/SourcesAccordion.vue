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
    
    <Transition name="accordion">
      <div v-show="expanded" class="accordion-content">
        <div class="chips-container">
          <SourceChip
            v-for="(src, i) in sources"
            :key="src.id"
            :chunk="src"
            class="source-chip-anim"
            :style="{ '--chip-delay': `${i * 40}ms` }"
          />
        </div>
      </div>
    </Transition>
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

/* Accordion expand/collapse: height + opacity reveal */
.accordion-enter-active,
.accordion-leave-active {
  transition: max-height var(--transition-normal) ease, opacity var(--transition-normal) ease, margin-top var(--transition-normal) ease;
  overflow: hidden;
}
.accordion-enter-from,
.accordion-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
}
.accordion-enter-to,
.accordion-leave-from {
  max-height: 400px;
  opacity: 1;
}

/* Each chip fades+slides in, staggered by --chip-delay */
.source-chip-anim {
  opacity: 0;
  transform: translateY(6px);
  animation: chipIn 0.3s ease forwards;
  animation-delay: var(--chip-delay, 0ms);
}
@keyframes chipIn {
  to { opacity: 1; transform: translateY(0); }
}
</style>
