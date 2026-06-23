<script setup>
import { computed } from 'vue';
import { useChunks } from '../composables/useChunks';
import { useChat } from '../composables/useChat';
import ChunkCard from './ChunkCard.vue';

const { enhancedChunks, baselineChunks } = useChunks();
const { compareWithBaseline } = useChat();

const enhancedChunksCompared = computed(() => {
  return enhancedChunks.value.map(chunk => {
    const baseChunk = baselineChunks.value.find(b => b.id === chunk.id);
    if (!baseChunk) {
      return {
        ...chunk,
        isNew: true,
        rankShift: ''
      };
    }
    const baseRank = baseChunk.rank;
    const enhancedRank = chunk.rank;
    let rankShift = '';
    if (enhancedRank < baseRank) {
      rankShift = 'up';
    } else if (enhancedRank > baseRank) {
      rankShift = 'down';
    }
    return {
      ...chunk,
      isNew: false,
      rankShift
    };
  });
});
</script>

<template>
  <div class="comparison-tab">
    <div v-if="!compareWithBaseline" class="compare-disabled">
      <div class="disabled-box glass-panel">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="var(--text-dim)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <h3>Comparison Mode Inactive</h3>
        <p>Enable the <strong>"Compare with baseline"</strong> checkbox below the input bar and submit a query to view side-by-side results.</p>
      </div>
    </div>
    
    <div v-else class="comparison-grid">
      <!-- Baseline Column -->
      <div class="compare-column baseline">
        <div class="column-header">
          <span class="col-title">Baseline</span>
          <span class="col-subtitle">(All flags off)</span>
        </div>
        <div class="column-cards">
          <div v-if="baselineChunks.length === 0" class="empty-col">
            No baseline chunks.
          </div>
          <ChunkCard
            v-for="chunk in baselineChunks"
            :key="chunk.id"
            :chunk="chunk"
          />
        </div>
      </div>
      
      <!-- Enhanced Column -->
      <div class="compare-column enhanced">
        <div class="column-header">
          <span class="col-title">Enhanced</span>
          <span class="col-subtitle">(Active flags)</span>
        </div>
        <div class="column-cards">
          <div v-if="enhancedChunksCompared.length === 0" class="empty-col">
            No enhanced chunks.
          </div>
          <ChunkCard
            v-for="chunk in enhancedChunksCompared"
            :key="chunk.id"
            :chunk="chunk"
            :is-new="chunk.isNew"
            :rank-shift="chunk.rankShift"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.compare-disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--spacing-lg);
}

.disabled-box {
  max-width: 320px;
  padding: var(--spacing-lg);
  text-align: center;
  background-color: rgba(17, 24, 39, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  border-color: var(--border-subtle);
}

.disabled-box h3 {
  font-size: 1rem;
  color: var(--text-primary);
}

.disabled-box p {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.disabled-box strong {
  color: var(--accent-secondary);
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100%;
  overflow: hidden;
}

.compare-column {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.compare-column.baseline {
  border-right: 1px solid var(--border-subtle);
}

.column-header {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  display: flex;
  flex-direction: column;
}

.col-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.baseline .col-title {
  color: var(--text-muted);
}

.enhanced .col-title {
  color: var(--accent-primary);
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}

.col-subtitle {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.column-cards {
  flex-grow: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.empty-col {
  font-size: 0.8rem;
  color: var(--text-dim);
  text-align: center;
  margin-top: var(--spacing-xl);
}
</style>
