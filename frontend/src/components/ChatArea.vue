<script setup>
import { computed } from 'vue';
import { useChat } from '../composables/useChat';
import MessageList from './MessageList.vue';
import SkeletonLoader from './SkeletonLoader.vue';
import ChatInput from './ChatInput.vue';

const { messages, isStreaming, sendQuery } = useChat();

const showSkeleton = computed(() => {
  if (!isStreaming.value) return false;
  const lastMsg = messages.value[messages.value.length - 1];
  return lastMsg && lastMsg.role === 'assistant' && !lastMsg.content;
});
</script>

<template>
  <main class="chat-area">
    <div class="chat-container">
      <MessageList :messages="messages" />
      <SkeletonLoader v-if="showSkeleton" />
      <ChatInput @send="sendQuery" />
    </div>
  </main>
</template>

<style scoped>
.chat-area {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-primary);
  position: relative;
}

.chat-container {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: var(--spacing-md) var(--spacing-md) 0 var(--spacing-md);
}
</style>
