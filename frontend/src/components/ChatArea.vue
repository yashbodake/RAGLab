<script setup>
import { computed } from 'vue';
import { useChat } from '../composables/useChat';
import MessageList from './MessageList.vue';
import SkeletonLoader from './SkeletonLoader.vue';
import ChatInput from './ChatInput.vue';

const {
  messages,
  isStreaming,
  suggestions,
  sendQuery,
  regenerate,
  exportPDF,
} = useChat();

const showSkeleton = computed(() => {
  if (isStreaming.value) return false;
  const lastMsg = messages.value[messages.value.length - 1];
  return lastMsg && lastMsg.role === 'assistant' && !lastMsg.content;
});

// Can regenerate only when not streaming and the last turn is a finished
// assistant answer (there's a prior user message to re-run).
const canRegenerate = computed(() => {
  if (isStreaming.value) return false;
  const n = messages.value.length;
  return n >= 2
    && messages.value[n - 1].role === 'assistant'
    && messages.value[n - 2].role === 'user';
});
</script>

<template>
  <main class="chat-area" :class="{ 'welcome-mode': messages.length === 0 }">
    <div class="chat-scroll">
      <div class="chat-canvas">
        <!-- State-zero welcome (only before first query) -->
        <section class="state-zero" v-if="messages.length === 0">
          <span class="welcome-eyebrow label-caps">Retrieval-Augmented Generation · Manuscript</span>
          <h1 class="welcome-headline">RAGLab_</h1>
        </section>

        <MessageList :messages="messages" />

        <!-- Action row: regenerate + export + follow-up suggestions -->
        <div v-if="messages.length > 0 && !isStreaming" class="action-row">
          <div class="action-row-top">
            <button
              v-if="canRegenerate"
              class="action-btn"
              @click="regenerate"
            >
              <span class="material-symbols-outlined">refresh</span>
              <span>REGENERATE</span>
            </button>

            <button
              v-if="messages.length > 0"
              class="action-btn"
              @click="exportPDF"
            >
              <span class="material-symbols-outlined">picture_as_pdf</span>
              <span>EXPORT PDF</span>
            </button>
          </div>

          <div v-if="suggestions.length > 0" class="suggestions">
            <span class="suggestions-label label-caps">FOLLOW-UP</span>
            <button
              v-for="(s, i) in suggestions"
              :key="i"
              class="suggestion-chip"
              @click="sendQuery(s)"
            >
              <span class="material-symbols-outlined">arrow_forward</span>
              <span>{{ s }}</span>
            </button>
          </div>
        </div>

        <SkeletonLoader v-if="showSkeleton" />
      </div>
    </div>

    <ChatInput :welcome="messages.length === 0" @send="sendQuery" />
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

/* In welcome mode (no messages yet): center the welcome content + input
   together as a group — like ChatGPT/Claude's landing screen. The input dock
   switches to position:relative (via the :welcome prop) so it flows here too. */
.chat-area.welcome-mode {
  justify-content: center;
}
.chat-area.welcome-mode .chat-scroll {
  flex: 0 0 auto;               /* don't grow — size to content */
  overflow: visible;
  padding: 0 var(--spacing-md);
}
/* The canvas must size to its content (not stretch to fill) so the centering
   has effect — without this it grabs the full height and stays at top. */
.chat-area.welcome-mode .chat-canvas {
  align-self: center;
  height: auto;
  flex: 0 0 auto;
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
.welcome-eyebrow {
  color: var(--accent-secondary);
  font-size: 11px;
  margin-bottom: var(--spacing-md);
  display: block;
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
  margin-bottom: var(--spacing-2xl);
}

/* ── Action row: regenerate + export + follow-up suggestions ─────── */
.action-row {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.action-row-top {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid rgba(7, 54, 66, 0.2);
  color: var(--text-muted);
  padding: 6px 10px;
  font-family: var(--font-mono);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.action-btn:hover {
  color: var(--accent-secondary);
  border-color: var(--accent-secondary);
}
.action-btn .material-symbols-outlined { font-size: 16px; }

.suggestions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  border-top: 1px dashed rgba(7, 54, 66, 0.15);
  padding-top: var(--spacing-md);
}
.suggestions-label {
  color: var(--text-dim);
  font-size: 10px;
  margin-bottom: var(--spacing-xs);
}
.suggestion-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  text-align: left;
  background: transparent;
  border: 1px solid rgba(7, 54, 66, 0.12);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.suggestion-chip:hover {
  border-color: var(--accent-secondary);
  background: rgba(203, 75, 22, 0.04);
}
.suggestion-chip .material-symbols-outlined {
  font-size: 16px;
  color: var(--accent-secondary);
  flex-shrink: 0;
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
