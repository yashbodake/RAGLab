<script setup>
import { computed } from 'vue';
import { useLayout } from '../composables/useLayout';

const props = defineProps({
  chunk: Object
});

const { inspectChunk } = useLayout();

const displayLabel = computed(() => {
  const meta = props.chunk.metadata || {};
  const code = meta.error_code ? ` [${meta.error_code}]` : '';
  const prod = meta.product ? ` ${meta.product}` : '';
  const src = (meta.source || 'doc').replace(/_/g, ' ');
  return `${props.chunk.rank}. ${src}${prod}${code}`;
});

const displayScore = computed(() => {
  const scores = props.chunk.scores || {};
  const s = scores.fused != null ? scores.fused : (scores.dense != null ? scores.dense : 0.0);
  return s.toFixed(3);
});
</script>

<template>
  <button class="source-chip glass-panel" @click="inspectChunk(chunk.id)">
    <span class="chip-label">{{ displayLabel }}</span>
    <span class="chip-score">{{ displayScore }}</span>
  </button>
</template>

<style scoped>
.source-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 4px var(--spacing-sm);
  border-radius: var(--radius-sm);
  background-color: var(--bg-panel);
  color: var(--text-muted);
  font-size: 0.78rem;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid rgba(7, 54, 66, 0.15);
  user-select: none;
  white-space: nowrap;
}

.source-chip:hover {
  color: var(--accent-secondary);
  border-color: var(--accent-secondary);
}

.chip-label {
  font-weight: 500;
}

.chip-score {
  font-family: var(--font-mono);
  background-color: rgba(7, 54, 66, 0.08);
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  font-size: 0.72rem;
  border: 1px solid rgba(7, 54, 66, 0.15);
  color: var(--text-dim);
}

.source-chip:hover .chip-score {
  color: var(--accent-secondary);
  border-color: var(--accent-secondary);
}
</style>
