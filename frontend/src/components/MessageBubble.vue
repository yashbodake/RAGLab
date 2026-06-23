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

    // Check headers
    const headerMatch = line.match(/^(\s*)(#{1,6})\s+(.*)/);
    if (headerMatch) {
      type = 'header';
      lineContent = headerMatch[3];
    }
    // Check unordered lists
    else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      type = 'list';
      lineContent = line.trim().substring(2);
    }
    // Check ordered lists
    else {
      const orderedMatch = line.match(/^\s*(\d+)\.\s+(.*)/);
      if (orderedMatch) {
        type = 'list';
        isOrdered = true;
        listNumber = orderedMatch[1];
        lineContent = orderedMatch[2];
      }
    }

    const segments = parseInline(lineContent);

    result.push({
      type,
      isOrdered,
      listNumber,
      segments
    });
  }
  return result;
});
</script>

<template>
  <div class="message-wrapper" :class="[role]">
    <div class="avatar" :class="[role]">
      <span v-if="role === 'user'">U</span>
      <span v-else>R</span>
    </div>
    
    <div class="bubble-container">
      <div class="message-bubble glass-panel" :class="[role]">
        <div class="bubble-content">
          <div v-for="(block, bIdx) in parsedBlocks" :key="bIdx" :class="block.type">
            <h4 v-if="block.type === 'header'" class="block-header">
              <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
                <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
                <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
                <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </h4>
            <p v-else-if="block.type === 'paragraph'" class="block-paragraph">
              <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
                <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
                <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
                <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </p>
            <li v-else-if="block.type === 'list'" class="block-list-item" :class="{ 'ordered': block.isOrdered }">
              <span v-if="block.isOrdered" class="list-number">{{ block.listNumber }}. </span>
              <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
                <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
                <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
                <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </li>
          </div>
          <span v-if="isStreaming" class="typing-cursor"></span>
        </div>
      </div>

      <!-- Expandable cited documents -->
      <SourcesAccordion v-if="role === 'assistant' && sources && sources.length > 0" :sources="sources" />
    </div>
  </div>
</template>

<style scoped>
.message-wrapper {
  display: flex;
  gap: var(--spacing-sm);
  max-width: 85%;
  margin-bottom: var(--spacing-sm);
  animation: fadeSlide 0.25s ease-out;
}

@keyframes fadeSlide {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
  border: 1px solid var(--border-subtle);
}

.avatar.user {
  background-color: var(--accent-secondary);
  color: #fff;
  border-color: rgba(255, 0, 127, 0.3);
  box-shadow: 0 0 8px rgba(255, 0, 127, 0.2);
}

.avatar.assistant {
  background-color: var(--bg-secondary);
  color: var(--accent-primary);
  border-color: var(--border-active);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}

.bubble-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex-grow: 1;
}

.message-bubble {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  line-height: 1.5;
  font-size: 0.95rem;
  word-break: break-word;
}

.message-bubble.user {
  background-color: rgba(255, 0, 127, 0.05);
  border-color: rgba(255, 0, 127, 0.2);
}

.message-bubble.user:hover {
  border-color: rgba(255, 0, 127, 0.4);
}

.message-bubble.assistant {
  background-color: rgba(255, 255, 255, 0.03);
}

.bubble-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.block-paragraph {
  white-space: pre-wrap;
}

.block-list-item {
  margin-left: var(--spacing-md);
  list-style-type: square;
}

.block-list-item.ordered {
  list-style-type: none;
  margin-left: var(--spacing-sm);
}

.list-number {
  color: var(--accent-primary);
  font-weight: 700;
  margin-right: 4px;
}

.inline-code {
  background-color: rgba(0, 240, 255, 0.1);
  color: var(--accent-primary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  border: 1px solid rgba(0, 240, 255, 0.2);
}

.bold-text {
  color: #fff;
  font-weight: 600;
}

.italic-text {
  font-style: italic;
}

.block-header {
  font-size: 1.05rem;
  font-weight: 700;
  margin-top: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
  color: var(--accent-primary);
}
</style>
