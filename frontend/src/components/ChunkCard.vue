<script setup>
import { ref } from 'vue';

defineProps({
  chunk: Object,
  isNew: { type: Boolean, default: false },
  rankShift: { type: String, default: '' }
});

const isExpanded = ref(false);

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
}
</script>

<template>
  <div :id="`chunk-card-${chunk.id}`" class="chunk-card glass-panel" :class="{ 'new-highlight': isNew }">
    <div class="card-header">
      <div class="rank-badge-wrapper">
        <div class="rank-badge">
          Rank {{ chunk.rank }}
          <span v-if="rankShift === 'up'" class="shift-arrow up" title="Moved up in rank">↑</span>
          <span v-if="rankShift === 'down'" class="shift-arrow down" title="Moved down in rank">↓</span>
        </div>
        <span v-if="isNew" class="new-badge">NEW</span>
      </div>
      <div class="chunk-id">{{ chunk.id }}</div>
    </div>
    
    <div class="chunk-body" :class="{ expanded: isExpanded }">
      {{ chunk.text }}
    </div>
    
    <button v-if="chunk.text && chunk.text.length > 150" class="expand-toggle-btn" @click="toggleExpand">
      {{ isExpanded ? 'Show Less' : 'Show More' }}
    </button>
    
    <div class="metadata-row">
      <span v-if="chunk.metadata?.source" class="meta-badge source">src: {{ chunk.metadata.source }}</span>
      <span v-if="chunk.metadata?.product" class="meta-badge product">prod: {{ chunk.metadata.product }}</span>
      <span v-if="chunk.metadata?.error_code" class="meta-badge error-code">code: {{ chunk.metadata.error_code }}</span>
      <span v-if="chunk.metadata?.chunk_index !== undefined" class="meta-badge index">chunk: {{ chunk.metadata.chunk_index }}</span>
    </div>
    
    <div class="scores-container">
      <!-- Dense score -->
      <div v-if="chunk.scores?.dense != null" class="score-row">
        <span class="score-label">Dense Cosine:</span>
        <div class="bar-outer">
          <div class="bar-inner dense" :style="{ width: `${chunk.scores.dense * 100}%` }"></div>
        </div>
        <span class="score-val">{{ chunk.scores.dense.toFixed(3) }}</span>
      </div>
      
      <!-- BM25 score -->
      <div v-if="chunk.scores?.bm25 != null" class="score-row">
        <span class="score-label">BM25 Sparse:</span>
        <div class="bar-outer">
          <div class="bar-inner bm25" :style="{ width: `${Math.min(chunk.scores.bm25 * 10, 100)}%` }"></div>
        </div>
        <span class="score-val">{{ chunk.scores.bm25.toFixed(3) }}</span>
      </div>
      
      <!-- Fused RRF Rank score -->
      <div v-if="chunk.scores?.fused != null" class="score-row">
        <span class="score-label">RRF Fused:</span>
        <div class="bar-outer">
          <div class="bar-inner fused" :style="{ width: `${chunk.scores.fused * 100}%` }"></div>
        </div>
        <span class="score-val">{{ chunk.scores.fused.toFixed(3) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chunk-card {
  padding: var(--spacing-md);
  background-color: var(--bg-panel);
  border-radius: var(--radius-md);
  border: 1px solid rgba(7, 54, 66, 0.18);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  transition: border-color var(--transition-fast);
}

.chunk-card:hover {
  border-color: var(--accent-secondary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rank-badge {
  background-color: rgba(7, 54, 66, 0.08);
  color: var(--accent-primary);
  border: 1px solid rgba(7, 54, 66, 0.2);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.chunk-id {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-dim);
}

.chunk-body {
  font-size: 0.85rem;
  color: var(--text-primary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.chunk-body.expanded {
  display: block;
  overflow: visible;
  -webkit-line-clamp: unset;
}

.expand-toggle-btn {
  background: none;
  border: none;
  color: var(--accent-primary);
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-start;
  padding: 0;
}

.expand-toggle-btn:hover {
  text-decoration: underline;
}

.metadata-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.meta-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}

.meta-badge.source {
  background-color: rgba(7, 54, 66, 0.06);
  color: var(--text-muted);
  border: 1px solid rgba(7, 54, 66, 0.15);
}

.meta-badge.product {
  background-color: rgba(42, 161, 152, 0.08);
  color: var(--accent-success);
  border: 1px solid rgba(42, 161, 152, 0.25);
}

.meta-badge.error-code {
  background-color: rgba(220, 50, 47, 0.08);
  color: var(--accent-error);
  border: 1px solid rgba(220, 50, 47, 0.25);
}

.meta-badge.index {
  background-color: rgba(181, 137, 0, 0.08);
  color: var(--accent-warning);
  border: 1px solid rgba(181, 137, 0, 0.25);
}

.scores-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-top: 4px;
  border-top: 1px solid rgba(7, 54, 66, 0.1);
  padding-top: var(--spacing-sm);
}

.score-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 0.75rem;
}

.score-label {
  color: var(--text-dim);
  width: 90px;
  font-weight: 500;
}

.bar-outer {
  flex-grow: 1;
  height: 6px;
  background-color: rgba(7, 54, 66, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
  border: 1px solid rgba(7, 54, 66, 0.12);
}

.bar-inner {
  height: 100%;
}

.bar-inner.dense {
  background-color: var(--accent-primary);
}

.bar-inner.bm25 {
  background-color: var(--accent-warning);
}

.bar-inner.fused {
  background-color: var(--accent-secondary);
}

.score-val {
  font-family: var(--font-mono);
  color: var(--text-muted);
  width: 45px;
  text-align: right;
}

/* Visual Flash animation for Targeted Inspect Card */
@keyframes highlightFlash {
  0% {
    border-color: var(--accent-secondary);
    box-shadow: 0 0 0 3px rgba(203, 75, 22, 0.25);
  }
  100% {
    border-color: rgba(7, 54, 66, 0.15);
    box-shadow: none;
  }
}

.highlight-flash {
  animation: highlightFlash 1.5s ease-out;
}

/* Comparison highlights */
.chunk-card.new-highlight {
  border-color: rgba(42, 161, 152, 0.45);
  background-color: rgba(42, 161, 152, 0.06);
}

.chunk-card.new-highlight:hover {
  border-color: var(--accent-success);
}

.rank-badge-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.shift-arrow {
  font-weight: 700;
  margin-left: 4px;
}

.shift-arrow.up {
  color: var(--accent-success);
}

.shift-arrow.down {
  color: var(--accent-error);
}

.new-badge {
  background-color: rgba(42, 161, 152, 0.1);
  color: var(--accent-success);
  border: 1px solid rgba(42, 161, 152, 0.3);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
