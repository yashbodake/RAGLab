<script setup>
import { ref, computed } from 'vue';
import { useChat } from '../composables/useChat';
import { useFeatures } from '../composables/useFeatures';
import MessageList from './MessageList.vue';
import SkeletonLoader from './SkeletonLoader.vue';
import ChatInput from './ChatInput.vue';

const { messages, isStreaming, sendQuery } = useChat();
const { features, toggleFeature } = useFeatures();

const showSkeleton = computed(() => {
  if (isStreaming.value) return false;
  const lastMsg = messages.value[messages.value.length - 1];
  return lastMsg && lastMsg.role === 'assistant' && !lastMsg.content;
});

// Feature grid is collapsed by default so the welcome screen stays clean —
// everything (headline + message + input hint) fits in one frame.
const featuresExpanded = ref(false);

// Count of currently-enabled features, for the badge.
const activeFeatureCount = computed(() =>
  Object.values(features).filter(Boolean).length
);

// The 7 retrieval features, surfaced as quick-toggle chips on the welcome
// screen. Same state (useFeatures) as the CONFIG modal — toggling here is
// reflected everywhere.
const featureChips = [
  { key: 'hybrid',              label: 'Hybrid Search',       hint: 'Dense + Sparse' },
  { key: 'query_understanding', label: 'Adaptive Routing',    hint: 'Query classification' },
  { key: 'metadata_aware',      label: 'Metadata Filter',     hint: 'Entity extraction' },
  { key: 'multi_index',         label: 'Multi-Index',         hint: 'Title + Body' },
  { key: 'remote_embed',        label: 'Remote Embed',        hint: 'Loopback service' },
  { key: 'hnsw',                label: 'HNSW Tuning',         hint: 'search_ef' },
  { key: 'stream_sources',      label: 'Stream Sources',      hint: 'Eager retrieval' },
];
</script>

<template>
  <main class="chat-area">
    <div class="chat-scroll">
      <div class="chat-canvas">
        <!-- State-zero welcome (only before first query) -->
        <section class="state-zero" v-if="messages.length === 0">
          <span class="welcome-eyebrow label-caps">Retrieval-Augmented Generation · Manuscript</span>
          <h1 class="welcome-headline">RAGLab_</h1>
          <p class="welcome-body">
            Enter your query into the manuscript terminal. Your inquiry will be
            retrieved, ranked, and synthesized across the industrial knowledge base.
          </p>

          <!-- Feature showcase — collapsed by default to keep the screen clean -->
          <div class="welcome-features">
            <button class="features-toggle" @click="featuresExpanded = !featuresExpanded">
              <span class="material-symbols-outlined chevron" :class="{ open: featuresExpanded }">expand_more</span>
              <span class="features-title label-caps">Configure Retrieval Techniques</span>
              <span class="features-badge" :class="{ has: activeFeatureCount > 0 }">{{ activeFeatureCount }}/7 active</span>
            </button>
            <Transition name="feature-expand">
              <div v-show="featuresExpanded" class="feature-grid">
                <button
                  v-for="feat in featureChips"
                  :key="feat.key"
                  class="feature-chip"
                  :class="{ active: features[feat.key] }"
                  @click="toggleFeature(feat.key)"
                >
                  <span class="chip-name">{{ feat.label }}</span>
                  <span class="chip-hint">{{ feat.hint }}</span>
                  <span class="chip-state" :class="{ on: features[feat.key] }">
                    {{ features[feat.key] ? 'ON' : 'OFF' }}
                  </span>
                </button>
              </div>
            </Transition>
          </div>
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

/* ── Feature showcase (collapsed by default) ─────────────────────── */
.welcome-features {
  border-top: 1px solid rgba(7, 54, 66, 0.12);
  padding-top: var(--spacing-lg);
}

.features-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  background: none;
  border: 1px solid rgba(7, 54, 66, 0.18);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.features-toggle:hover {
  border-color: var(--accent-secondary);
  background: rgba(203, 75, 22, 0.03);
}

.chevron {
  font-size: 20px;
  color: var(--text-muted);
  transition: transform var(--transition-fast);
}
.chevron.open {
  transform: rotate(180deg);
  color: var(--accent-secondary);
}

.features-title {
  color: var(--accent-primary);
  font-size: 12px;
  flex: 1;
  text-align: left;
}

.features-badge {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-dim);
  border: 1px solid rgba(7, 54, 66, 0.2);
  padding: 2px 6px;
}
.features-badge.has {
  color: var(--accent-secondary);
  border-color: var(--accent-secondary);
}

/* Expand/collapse transition */
.feature-expand-enter-active,
.feature-expand-leave-active {
  transition: opacity var(--transition-normal) ease;
  overflow: hidden;
}
.feature-expand-enter-from,
.feature-expand-leave-to {
  opacity: 0;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.feature-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  text-align: left;
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: 1px solid rgba(7, 54, 66, 0.18);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}
.feature-chip:hover {
  border-color: var(--accent-secondary);
  background: rgba(203, 75, 22, 0.03);
}
.feature-chip.active {
  border-color: var(--accent-primary);
  background: rgba(7, 54, 66, 0.05);
}

.chip-name {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}
.chip-hint {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.04em;
  color: var(--text-dim);
}
.chip-state {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-md);
  font-family: var(--font-mono);
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--text-dim);
}
.chip-state.on {
  color: var(--accent-secondary);
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
  .feature-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>
