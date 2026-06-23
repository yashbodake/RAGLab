<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import { useLogs } from '../composables/useLogs';
import LogEntry from './LogEntry.vue';

const { logEntries, clearLogs } = useLogs();
const containerRef = ref(null);

function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight;
    }
  });
}

watch(() => logEntries.value.length, scrollToBottom);
onMounted(scrollToBottom);
</script>

<template>
  <div class="log-stream-tab">
    <div class="tab-header">
      <span class="tab-title">Pipeline Traces</span>
      <button class="clear-btn" @click="clearLogs">Clear</button>
    </div>
    
    <div class="log-container" ref="containerRef">
      <div v-if="logEntries.length === 0" class="empty-logs">
        No active pipeline events. Submit a query to see logs.
      </div>
      <LogEntry
        v-for="(log, idx) in logEntries"
        :key="idx"
        :timestamp="log.timestamp"
        :stage="log.stage"
        :message="log.message"
        :level="log.level"
      />
    </div>
  </div>
</template>

<style scoped>
.log-stream-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.tab-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}

.clear-btn {
  background: none;
  border: 1px solid var(--border-subtle);
  color: var(--text-dim);
  font-family: var(--font-body);
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  color: var(--text-primary);
  border-color: rgba(255, 255, 255, 0.2);
}

.log-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: var(--spacing-sm) 0;
  display: flex;
  flex-direction: column;
}

.empty-logs {
  padding: var(--spacing-md);
  font-size: 0.8rem;
  color: var(--text-dim);
  text-align: center;
  margin-top: var(--spacing-xl);
}
</style>
