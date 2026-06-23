<script setup>
import { computed } from 'vue';
import SourcesAccordion from './SourcesAccordion.vue';

const props = defineProps({
  role: String, // 'user' | 'assistant'
  content: String,
  sources: Array,
  isStreaming: Boolean
});

function parseInline(text) {
  const segments = [];
  let remaining = text;

  while (remaining) {
    const codeMatch = remaining.match(/`([^`\n]+)`/);
    const boldAsteriskMatch = remaining.match(/\*\*([^*\n]+)\*\*/);
    const boldUnderscoreMatch = remaining.match(/__([^\n_]+)__/);
    const italicAsteriskMatch = remaining.match(/\*([^*\n]+)\*/);
    const italicUnderscoreMatch = remaining.match(/_([^\n_]+)_/);

    let firstMatch = null;
    let matchType = '';
    let startIndex = -1;
    let matchLength = 0;
    let matchText = '';

    const checkMatch = (match, type) => {
      if (match && (startIndex === -1 || match.index < startIndex)) {
        firstMatch = match;
        matchType = type;
        startIndex = match.index;
        matchLength = match[0].length;
        matchText = match[1];
      }
    };

    checkMatch(codeMatch, 'code');
    checkMatch(boldAsteriskMatch, 'bold');
    checkMatch(boldUnderscoreMatch, 'bold');
    checkMatch(italicAsteriskMatch, 'italic');
    checkMatch(italicUnderscoreMatch, 'italic');

    if (firstMatch !== null) {
      if (startIndex > 0) {
        segments.push({ type: 'text', text: remaining.substring(0, startIndex) });
      }
      segments.push({ type: matchType, text: matchText });
      remaining = remaining.substring(startIndex + matchLength);
    } else {
      segments.push({ type: 'text', text: remaining });
      break;
    }
  }
  return segments;
}

const parsedBlocks = computed(() => {
  if (!props.content) return [];
  const lines = props.content.split('\n');
  const result = [];

  for (const line of lines) {
    let type = 'paragraph';
    let isOrdered = false;
    let listNumber = '';
    let lineContent = line;

    const headerMatch = line.match(/^(\s*)(#{1,6})\s+(.*)/);
    if (headerMatch) {
      type = 'header';
      lineContent = headerMatch[3];
    } else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      type = 'list';
      lineContent = line.trim().substring(2);
    } else {
      const orderedMatch = line.match(/^\s*(\d+)\.\s+(.*)/);
      if (orderedMatch) {
        type = 'list';
        isOrdered = true;
        listNumber = orderedMatch[1];
        lineContent = orderedMatch[2];
      }
    }

    const segments = parseInline(lineContent);

    result.push({ type, isOrdered, listNumber, segments });
  }
  return result;
});

// Index of the first paragraph block — used to apply the drop-cap.
const firstParagraphIndex = computed(() =>
  parsedBlocks.value.findIndex(b => b.type === 'paragraph')
);
</script>

<template>
  <article class="message" :class="[role]">

    <!-- ── USER: manuscript input card ─────────────────────────────── -->
    <template v-if="role === 'user'">
      <div class="user-card">
        <span class="user-label label-caps">USER_INPUT // {{ new Date().toLocaleTimeString('en-GB') }}</span>
        <p class="user-text">{{ content }}</p>
      </div>
    </template>

    <!-- ── ASSISTANT: Aether synthesis ─────────────────────────────── -->
    <template v-else>
      <div class="synthesis-head">
        <span class="material-symbols-outlined synthesis-icon" :class="{ 'fade-pulse': isStreaming }">auto_awesome</span>
        <span class="synthesis-label label-caps">{{ isStreaming && !content ? 'AETHER_SYNTHESIS_THINKING' : 'AETHER_SYNTHESIS' }}</span>
      </div>

      <div class="synthesis-body">
        <div v-for="(block, bIdx) in parsedBlocks" :key="bIdx" :class="['block', block.type]">

          <h4 v-if="block.type === 'header'" class="block-header">
            <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
              <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
              <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
              <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </h4>

          <p
            v-else-if="block.type === 'paragraph'"
            class="block-paragraph"
            :class="{ 'drop-cap': bIdx === firstParagraphIndex && parsedBlocks.length > 1 }"
          >
            <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
              <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
              <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
              <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </p>

          <div v-else-if="block.type === 'list'" class="block-list-item" :class="{ ordered: block.isOrdered }">
            <span v-if="block.isOrdered" class="list-number">{{ block.listNumber }}_</span>
            <span v-else class="list-bullet">▸</span>
            <span class="list-content">
              <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
                <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
                <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
                <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </span>
          </div>
        </div>

        <span v-if="isStreaming" class="typing-cursor"></span>
      </div>

      <!-- Expandable cited documents -->
      <SourcesAccordion v-if="role === 'assistant' && sources && sources.length > 0" :sources="sources" />
    </template>

  </article>
</template>

<style scoped>
.message {
  width: 100%;
  animation: fadeSlide 0.25s ease-out;
}

/* ── USER card ─────────────────────────────────────────────────────── */
.user-card {
  position: relative;
  background: rgba(245, 239, 220, 0.45);
  border: 1px solid rgba(7, 54, 66, 0.12);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
}
.user-label {
  position: absolute;
  top: -9px;
  left: var(--spacing-md);
  background: var(--bg-primary);
  padding: 0 6px;
  font-size: 9px;
  color: rgba(7, 54, 66, 0.55);
}
.user-text {
  font-family: var(--font-body);
  font-size: 1.05rem;
  line-height: 1.6;
  font-style: italic;
  color: rgba(7, 54, 66, 0.9);
}

/* ── ASSISTANT synthesis ───────────────────────────────────────────── */
.synthesis-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}
.synthesis-icon {
  font-size: 22px;
  color: var(--accent-secondary);
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
.synthesis-label {
  color: var(--accent-primary);
  font-size: 12px;
}

.synthesis-body {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.7;
  color: rgba(7, 54, 66, 0.9);
}
.synthesis-body .block + .block { margin-top: var(--spacing-md); }

.block-header {
  font-family: var(--font-headline);
  font-weight: 700;
  font-size: 1.5rem;
  line-height: 1.25;
  color: var(--accent-primary);
  margin: var(--spacing-lg) 0 var(--spacing-sm);
}

.block-paragraph { color: rgba(7, 54, 66, 0.9); }

.block-list-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: 4px 0;
}
.block-list-item.ordered {
  font-family: var(--font-mono);
  font-size: 0.9rem;
}
.list-number {
  color: var(--accent-secondary);
  font-weight: 700;
  flex-shrink: 0;
  min-width: 28px;
}
.list-bullet {
  color: var(--accent-secondary);
  flex-shrink: 0;
}
.list-content { flex: 1; }

/* Inline formatting */
.inline-code {
  font-family: var(--font-mono);
  font-size: 0.88em;
  background: rgba(7, 54, 66, 0.08);
  border: 1px solid rgba(7, 54, 66, 0.12);
  padding: 1px 5px;
  color: var(--accent-primary);
}
.bold-text { font-weight: 700; color: var(--accent-primary); }
.italic-text { font-style: italic; }

@keyframes fadeSlide {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
