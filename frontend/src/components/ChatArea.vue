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
    <div class="chat-scroll">
      <div class="chat-canvas">
        <!-- State-zero welcome (only before first query) -->
        <section class="state-zero" v-if="messages.length === 0">
          <h1 class="welcome-headline">RAGLab_</h1>
          <p class="welcome-body">
            Enter your query into the manuscript terminal. Your inquiry will be
            retrieved, ranked, and synthesized across the industrial knowledge base.
          </p>
        </section>

        <MessageList :messages="messages" />
        <SkeletonLoader v-if="showSkeleton" />
      </div>
    </div>

    <ChatInput @send="sendQuery" />
  </main>
</template>

<style scoped>
.chat-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: var(--bg-primary);
  position: relative;
}

.chat-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--spacing-2xl) var(--spacing-md) 180px;
}

.chat-canvas {
  max-width: var(--canvas-max-width);
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

/* State-zero welcome */
.state-zero {
  padding: var(--spacing-lg) var(--spacing-sm);
}
.welcome-headline {
  font-family: var(--font-headline);
  font-weight: 700;
  font-size: clamp(2rem, 5vw, 3rem);
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: var(--accent-primary);
  margin-bottom: var(--spacing-lg);
}
.welcome-body {
  font-family: var(--font-body);
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-muted);
  max-width: 540px;
}

/* ── Mobile: tighter padding, less room reserved for the dock ────── */
@media (max-width: 600px) {
  .chat-scroll {
    padding: var(--spacing-lg) var(--spacing-sm) 140px;
  }
  .state-zero {
    padding: var(--spacing-md) var(--spacing-xs);
  }
  .welcome-body {
    font-size: 0.95rem;
  }
}
</style>
