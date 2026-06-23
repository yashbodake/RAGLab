<script setup>
import { useChunks } from '../composables/useChunks';
import ChunkCard from './ChunkCard.vue';

const { enhancedChunks } = useChunks();
</script>

<template>
  <div class="chunk-inspector-tab">
    <div class="tab-header">
      <span class="tab-title">Retrieved Chunks</span>
    </div>
    
    <div class="chunks-container">
      <div v-if="enhancedChunks.length === 0" class="empty-chunks">
        No active retrieved document chunks. Submit a query to inspect.
      </div>
      <ChunkCard
        v-for="chunk in enhancedChunks"
        :key="chunk.id"
        :chunk="chunk"
      />
    </div>
  </div>
</template>

<style scoped>
.chunk-inspector-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-header {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid rgba(7, 54, 66, 0.12);
}

.tab-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}

.chunks-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.empty-chunks {
  font-size: 0.8rem;
  color: var(--text-dim);
  text-align: center;
  margin-top: var(--spacing-xl);
}
</style>
