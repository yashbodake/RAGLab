<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useChat } from '../composables/useChat';
import { useFeatures } from '../composables/useFeatures';

defineProps({
  // When true (no messages yet), the dock flows in normal layout right under
  // the centered welcome content instead of being pinned to the viewport bottom.
  welcome: { type: Boolean, default: false }
});

const emit = defineEmits(['send']);

const query = ref('');
const textareaRef = ref(null);
const { isStreaming, compareWithBaseline, stopGeneration } = useChat();
const { features, toggleFeature } = useFeatures();

// Feature tray open/closed — the + button morphs to X.
const featuresOpen = ref(false);

const activeFeatureCount = computed(() =>
  Object.values(features).filter(Boolean).length
);

// The 7 retrieval features as creative toggle pills (icon + label, no checkboxes).
const featurePills = [
  { key: 'hybrid',              icon: 'merge',         label: 'Hybrid' },
  { key: 'query_understanding', icon: 'alt_route',     label: 'Routing' },
  { key: 'metadata_aware',      icon: 'filter_alt',    label: 'Metadata' },
  { key: 'multi_index',         icon: 'view_module',   label: 'Multi-Index' },
  { key: 'remote_embed',        icon: 'cloud_sync',    label: 'Remote Embed' },
  { key: 'hnsw',                icon: 'tune',          label: 'HNSW' },
  { key: 'stream_sources',      icon: 'bolt',          label: 'Eager Sources' },
];

function handleSend() {
  if (!query.value.trim() || isStreaming.value) return;
  emit('send', query.value);
  query.value = '';
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
  }
}

// Enter sends when idle; while streaming, Enter stops generation (handy with
// the morphing button) so users have a keyboard shortcut for stop too.
function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (isStreaming.value) {
      stopGeneration();
    } else {
      handleSend();
    }
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
  <div class="input-dock" :class="{ 'welcome-mode': welcome }">
    <!-- Feature pill tray — expands above the input when the + is toggled -->
    <Transition name="tray">
      <div v-if="featuresOpen" class="feature-tray">
        <div class="tray-inner">
          <span class="tray-label label-caps">RETRIEVAL TECHNIQUES</span>
          <div class="pill-row">
            <button
              v-for="f in featurePills"
              :key="f.key"
              class="feat-pill"
              :class="{ on: features[f.key] }"
              @click="toggleFeature(f.key)"
              :aria-pressed="features[f.key]"
            >
              <span class="material-symbols-outlined pill-icon">{{ f.icon }}</span>
              <span class="pill-label">{{ f.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <div class="input-frame">
      <!-- Left: + / X toggle (morphs). Shows a count badge when features active. -->
      <button
        class="feature-toggle"
        :class="{ open: featuresOpen }"
        @click="featuresOpen = !featuresOpen"
        :aria-label="featuresOpen ? 'Hide features' : 'Show features'"
      >
        <span class="material-symbols-outlined">{{ featuresOpen ? 'close' : 'add' }}</span>
        <span v-if="activeFeatureCount > 0 && !featuresOpen" class="feat-badge">{{ activeFeatureCount }}</span>
      </button>

      <textarea
        ref="textareaRef"
        v-model="query"
        placeholder="Inquire the RAGLab..."
        rows="1"
        class="input-textarea"
        @keydown="handleKeyDown"
      ></textarea>

      <!-- Send / Stop: the same button slot morphs between send (arrow) and
           stop (square) based on streaming state — like ChatGPT/Claude. -->
      <button
        v-if="!isStreaming"
        class="send-button"
        :class="{ active: query.trim() }"
        :disabled="!query.trim()"
        aria-label="Send Query"
        @click="handleSend"
      >
        <span class="material-symbols-outlined">north</span>
      </button>
      <button
        v-else
        class="send-button stop-button"
        aria-label="Stop generating"
        @click="stopGeneration"
      >
        <span class="material-symbols-outlined">stop</span>
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
  /* Mask the position-flip between welcome (relative/centered) and chat
     (absolute/bottom) with a quick transform+opacity transition. `position`
     itself can't animate, so this gives the eye a smooth handoff. */
  transition: transform var(--transition-normal), opacity var(--transition-normal);
}

/* Welcome mode: stop pinning to the bottom — flow in normal layout so the
   dock sits directly under the vertically-centered welcome content. */
.input-dock.welcome-mode {
  position: relative;
  bottom: auto;
  left: auto;
  right: auto;
  background: transparent;
}

/* ── Feature pill tray (overlays above the input bar) ────────────── */
/* Absolutely positioned so opening/closing it (+/X) never pushes the bar or
   the dock layout — it floats above the input frame instead. */
.feature-tray {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(100% + var(--spacing-sm));
  width: 768px;
  max-width: calc(100vw - 2 * var(--spacing-md));
  background: #ffffff;
  border: 1px solid #000000;
  box-shadow: 4px 4px 0 0 rgba(7, 54, 66, 1);
  padding: var(--spacing-sm) var(--spacing-md);
  pointer-events: auto;
}
.tray-inner {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.tray-label {
  color: var(--text-dim);
  font-size: 9px;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}
.feat-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: transparent;
  border: 1px solid rgba(7, 54, 66, 0.2);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.feat-pill:hover {
  border-color: var(--accent-secondary);
  color: var(--accent-secondary);
}
/* Active state: terracotta filled pill */
.feat-pill.on {
  background: var(--accent-secondary);
  border-color: var(--accent-secondary);
  color: #fff;
}
.pill-icon { font-size: 14px; }

/* Tray expand/collapse animation */
.tray-enter-active, .tray-leave-active {
  transition: opacity var(--transition-normal), transform var(--transition-normal);
  transform-origin: bottom center;
}
.tray-enter-from, .tray-leave-to {
  opacity: 0;
  transform: translateY(8px) scaleY(0.9);
}

/* ── +/X feature toggle button (left of input) ───────────────────── */
.feature-toggle {
  position: relative;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #000;
  border: none;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.feature-toggle:hover { color: var(--accent-secondary); }
.feature-toggle .material-symbols-outlined { font-size: 22px; transition: transform var(--transition-fast); }
.feature-toggle.open {
  background: var(--accent-secondary);
  color: #fff;
}
.feature-toggle.open .material-symbols-outlined { transform: rotate(90deg); }

/* Count badge on the + button when features are active */
.feat-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-secondary);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  border-radius: 8px;
}

.input-frame {
  /* Fixed standard size: 768px wide x 56px tall is the conventional chat
     input dimension (ChatGPT/Claude use ~768px). Locked so it doesn't
     shrink/grow between welcome mode and chat mode. */
  width: 768px;
  max-width: 100%;
  min-height: 56px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: #ffffff;
  border: 1px solid #000000;
  box-shadow: 8px 8px 0 0 rgba(7, 54, 66, 1);
  padding: 0 var(--spacing-sm) 0 var(--spacing-lg);
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
  padding: 16px 0;          /* fixed padding keeps the bar a consistent height */
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

/* Stop button: terracotta square in the send-button slot while streaming */
.stop-button {
  background: var(--accent-secondary);
  color: #fff;
  animation: stopBtnPulse 1.6s ease-in-out infinite;
}
.stop-button:hover { background: #b03e10; }
.stop-button .material-symbols-outlined { font-size: 18px; font-variation-settings: 'FILL' 1; }
@keyframes stopBtnPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(203, 75, 22, 0.5); }
  50% { box-shadow: 0 0 0 6px rgba(203, 75, 22, 0); }
}

/* ── Tablet: scale the bar down from the fixed 768px ─────────────── */
@media (max-width: 900px) and (min-width: 601px) {
  .input-frame {
    width: calc(100vw - 2 * var(--spacing-xl));
    max-width: 768px;
  }
}

/* ── Mobile: full-width dock, reduced shadow/padding ────────────── */
@media (max-width: 600px) {
  .input-dock {
    padding: var(--spacing-md) var(--spacing-sm) var(--spacing-sm);
  }
  .input-frame {
    /* Fit the mobile viewport: full width minus side margins, and shrink the
       hard shadow so it doesn't overflow the screen edge. */
    width: calc(100vw - 2 * var(--spacing-md));
    max-width: calc(100vw - 2 * var(--spacing-md));
    min-height: 56px;
    box-shadow: 4px 4px 0 0 rgba(7, 54, 66, 1);
    gap: var(--spacing-sm);
  }
  .input-frame:focus-within {
    box-shadow: 3px 3px 0 0 var(--accent-secondary);
  }
  .input-textarea {
    font-size: 16px; /* 16px prevents iOS zoom-on-focus */
    padding: 16px 0; /* keep consistent bar height */
  }
  .send-button {
    width: 36px;
    height: 36px;
    flex-shrink: 0;
  }
  .feature-toggle {
    width: 36px;
    height: 36px;
    flex-shrink: 0;
  }
  /* Stack the meta row: compare toggle above the hint, both centered */
  .input-meta {
    flex-direction: column;
    gap: var(--spacing-xs);
    align-items: flex-start;
  }
  .hint { display: none; }
}

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
