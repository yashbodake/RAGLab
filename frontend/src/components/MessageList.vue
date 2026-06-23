<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import MessageBubble from './MessageBubble.vue';

const props = defineProps({
  messages: Array
});

const listRef = ref(null);

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  });
}

watch(() => props.messages.length, scrollToBottom);

watch(() => {
  if (props.messages.length === 0) return '';
  return props.messages[props.messages.length - 1].content;
}, scrollToBottom);

onMounted(scrollToBottom);
</script>

<template>
  <div class="message-list" ref="listRef">
    <div v-if="messages.length === 0" class="empty-state">
      <div class="welcome-box glass-panel">
        <h2>Industrial RAG Sandbox</h2>
        <p>This sandbox implements a 7-stage advanced retrieval pipeline utilizing Chroma vector DB, BM25 indices, and the Cerebras LLaMA-3.1 API.</p>
        <div class="tip">
          <strong>Sample Queries:</strong>
          <ul>
            <li>"What is the power output of E452 vs E501?"</li>
            <li>"How to troubleshoot system pressure warnings on switch E415?"</li>
          </ul>
        </div>
      </div>
    </div>
    <MessageBubble
      v-for="msg in messages"
      :key="msg.id"
      :role="msg.role"
      :content="msg.content"
      :sources="msg.sources"
      :is-streaming="msg.isStreaming"
    />
  </div>
</template>

<style scoped>
.message-list {
  flex-grow: 1;
  overflow-y: auto;
  padding-bottom: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.welcome-box {
  max-width: 500px;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  text-align: center;
  background-color: rgba(17, 24, 39, 0.5);
  border-color: var(--border-subtle);
}

.welcome-box h2 {
  font-size: 1.3rem;
  color: var(--accent-primary);
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
}

.welcome-box p {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
}

.tip {
  text-align: left;
  border-top: 1px solid var(--border-subtle);
  padding-top: var(--spacing-md);
  font-size: 0.85rem;
}

.tip strong {
  color: var(--text-primary);
  display: block;
  margin-bottom: var(--spacing-xs);
}

.tip ul {
  padding-left: var(--spacing-md);
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
</style>
