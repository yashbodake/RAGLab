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
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
  }
}

function handleKeyDown(e) {
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
  <div class="input-dock">
    <div class="input-frame">
      <textarea
        ref="textareaRef"
        v-model="query"
        placeholder="Inquire the Aether Archive..."
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
        <span class="material-symbols-outlined">north</span>
      </button>
    </div>

    <div class="input-meta">
      <label class="compare-toggle" :class="{ disabled: isStreaming }">
        <input
          type="checkbox"
          v-model="compareWithBaseline"
          :disabled="isStreaming"
          class="compare-checkbox"
        />
        <span class="compare-text">COMPARE_WITH_BASELINE</span>
      </label>
      <span class="hint">↵ SEND · ⇧↵ NEWLINE</span>
    </div>
  </div>
</template>

<style scoped>
/* Floating bottom dock — inspiration's centered bar with hard shadow */
.input-dock {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: var(--spacing-lg) var(--spacing-md) var(--spacing-md);
  background: linear-gradient(to top, var(--bg-primary) 55%, rgba(253, 246, 227, 0));
  pointer-events: none;
  z-index: 20;
}

.input-frame {
  max-width: var(--canvas-max-width);
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-md);
  background: #ffffff;
  border: 1px solid #000000;
  box-shadow: 8px 8px 0 0 rgba(7, 54, 66, 1);
  padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) var(--spacing-lg);
  pointer-events: auto;
  transition: box-shadow var(--transition-fast);
}
.input-frame:focus-within {
  box-shadow: 6px 6px 0 0 var(--accent-secondary);
}

.input-textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-family: var(--font-mono);
  font-size: 0.95rem;
  line-height: 1.5;
  color: #000000;
  padding: 10px 0;
  max-height: 200px;
  overflow-y: auto;
}
.input-textarea::placeholder { color: rgba(0, 0, 0, 0.3); }
.input-textarea:disabled { opacity: 0.5; }

.send-button {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000000;
  color: #ffffff;
  border: none;
  cursor: pointer;
  transition: background var(--transition-fast), transform var(--transition-fast);
}
.send-button .material-symbols-outlined { font-size: 20px; }
.send-button:disabled { opacity: 0.25; cursor: not-allowed; }
.send-button:not(:disabled):active { transform: scale(0.88); }
.send-button.active:hover { background: var(--accent-secondary); }

/* Meta row */
.input-meta {
  max-width: var(--canvas-max-width);
  margin: var(--spacing-sm) auto 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  pointer-events: auto;
}

.compare-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  user-select: none;
}
.compare-toggle.disabled { opacity: 0.5; cursor: not-allowed; }

.compare-checkbox {
  appearance: none;
  width: 14px;
  height: 14px;
  border: 1px solid var(--accent-primary);
  background: transparent;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.compare-checkbox:checked {
  background: var(--accent-secondary);
  border-color: var(--accent-secondary);
}
.compare-checkbox:checked::after {
  content: '✓';
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.compare-text {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-muted);
}

.hint {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  color: rgba(7, 54, 66, 0.35);
}
</style>
