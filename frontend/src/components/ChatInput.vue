<script setup>
import { ref, watch, nextTick } from 'vue';
import { useChat } from '../composables/useChat';

const emit = defineEmits(['send']);

const query = ref('');
const textareaRef = ref(null);
const { isStreaming, compareWithBaseline } = useChat();

function handleSend() {
  if (!query.value.trim() || isStreaming.value) return;
  emit('send', query.value);
  query.value = '';
  // Reset height
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
  }
}

function handleKeyDown(e) {
  // Submit on Enter without Shift
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

// Auto-grow textarea
watch(query, () => {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto';
      textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px';
    }
  });
});
</script>

<template>
  <div class="chat-input-wrapper glass-panel">
    <div class="input-row">
      <textarea
        ref="textareaRef"
        v-model="query"
        placeholder="Ask a technical or maintenance question..."
        rows="1"
        class="input-textarea"
        :disabled="isStreaming"
        @keydown="handleKeyDown"
      ></textarea>
      
      <button
        class="send-button"
        :class="{ active: query.trim() && !isStreaming }"
        :disabled="!query.trim() || isStreaming"
        aria-label="Send Query"
        @click="handleSend"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
    
    <div class="input-controls">
      <label class="compare-toggle">
        <input
          type="checkbox"
          v-model="compareWithBaseline"
          :disabled="isStreaming"
          class="compare-checkbox"
        />
        <span class="compare-text">Compare with baseline (no RAG enhancements)</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.chat-input-wrapper {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border-color: var(--border-subtle);
  transition: all var(--transition-normal);
}

.chat-input-wrapper:focus-within {
  border-color: var(--border-active);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.15);
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
}

.input-textarea {
  flex-grow: 1;
  background: none;
  border: none;
  resize: none;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.95rem;
  padding: var(--spacing-sm) 0;
  max-height: 200px;
  line-height: 1.4;
  outline: none;
}

.input-textarea::placeholder {
  color: var(--text-dim);
}

.input-textarea:disabled {
  color: var(--text-dim);
}

.send-button {
  background-color: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  color: var(--text-dim);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
  margin-bottom: 2px;
}

.send-button.active {
  background-color: var(--accent-primary);
  color: var(--bg-primary);
  border-color: var(--accent-primary);
  box-shadow: 0 0 8px var(--accent-primary);
}

.send-button.active:hover {
  background-color: #00d8e6;
  box-shadow: 0 0 12px var(--accent-primary);
}

.send-button:disabled {
  cursor: not-allowed;
}

.input-controls {
  display: flex;
  align-items: center;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.03);
}

.compare-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  user-select: none;
}

.compare-checkbox {
  accent-color: var(--accent-secondary);
  cursor: pointer;
}

.compare-text {
  font-size: 0.8rem;
  color: var(--text-dim);
  transition: color var(--transition-fast);
}

.compare-toggle:hover .compare-text {
  color: var(--text-muted);
}
</style>
