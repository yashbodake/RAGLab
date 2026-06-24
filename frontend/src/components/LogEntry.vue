<script setup>
import { computed } from 'vue';

const props = defineProps({
  timestamp: String,
  stage: String,
  message: String,
  level: { type: String, default: 'info' }
});

const displayTime = computed(() => {
  if (!props.timestamp) return '';
  // Show only HH:MM:SS.mmm
  try {
    const parts = props.timestamp.split('T');
    if (parts.length > 1) {
      return parts[1].replace('Z', '');
    }
  } catch (e) {}
  return props.timestamp;
});
</script>

<template>
  <div class="log-entry" :class="[level]">
    <span class="log-time">{{ displayTime }}</span>
    <span class="log-stage">[{{ stage }}]</span>
    <span class="log-msg">{{ message }}</span>
  </div>
</template>

<style scoped>
.log-entry {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  line-height: 1.4;
  padding: 4px var(--spacing-sm);
  border-left: 2px solid transparent;
  display: flex;
  gap: var(--spacing-sm);
  word-break: break-all;
  transition: background-color var(--transition-fast);
  animation: logIn 0.35s ease both;
}

/* New log lines slide in from the left + fade — terminal-trace feel */
@keyframes logIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

.log-entry:hover {
  background-color: var(--bg-panel-hover);
}

.log-time {
  color: var(--text-dim);
  flex-shrink: 0;
}

.log-stage {
  color: var(--accent-primary);
  font-weight: 500;
  flex-shrink: 0;
  text-transform: uppercase;
}

.log-msg {
  color: var(--text-primary);
}

/* Level Colorings */
.log-entry.info {
  border-left-color: var(--border-subtle);
}

.log-entry.warn {
  border-left-color: var(--accent-warning);
}
.log-entry.warn .log-msg {
  color: var(--accent-warning);
}

.log-entry.error {
  border-left-color: var(--accent-error);
}
.log-entry.error .log-msg {
  color: var(--accent-error);
}

.log-entry.debug {
  border-left-color: var(--text-dim);
}
.log-entry.debug .log-msg {
  color: var(--text-muted);
}
</style>
