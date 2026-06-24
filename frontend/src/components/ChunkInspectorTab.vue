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

/* Staggered fade-up cascade when chunks arrive (dealing-cards feel) */
.chunks-container > * {
  animation: chunkIn 0.4s ease both;
  animation-delay: calc(var(--i, 0) * 60ms);
}
.chunks-container > :nth-child(1) { --i: 0; }
.chunks-container > :nth-child(2) { --i: 1; }
.chunks-container > :nth-child(3) { --i: 2; }
.chunks-container > :nth-child(4) { --i: 3; }
.chunks-container > :nth-child(5) { --i: 4; }
.chunks-container > :nth-child(6) { --i: 5; }
.chunks-container > :nth-child(7) { --i: 6; }
.chunks-container > :nth-child(8) { --i: 7; }
.chunks-container > :nth-child(n+9) { --i: 8; }

@keyframes chunkIn {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-chunks {
  font-size: 0.8rem;
  color: var(--text-dim);
  text-align: center;
  margin-top: var(--spacing-xl);
}
</style>
