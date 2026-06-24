<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import MessageBubble from './MessageBubble.vue';

const props = defineProps({
  messages: Array
});

const listRef = ref(null);
let scrollContainer = null;

// The scroll container is NOT .message-list (that just flows) — it's the
// nearest scrollable ancestor (.chat-scroll in ChatArea). Find it once.
function findScrollContainer() {
  let el = listRef.value?.parentElement;
  while (el) {
    const style = getComputedStyle(el);
    if (/(auto|scroll)/.test(style.overflowY)) {
      return el;
    }
    el = el.parentElement;
  }
  return null;
}

// Only auto-scroll if the user is already near the bottom — so we don't
// yank the view away while they're reading earlier content.
function isNearBottom() {
  if (!scrollContainer) return true;
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
  return scrollHeight - scrollTop - clientHeight < 120;
}

function scrollToBottom() {
  if (!scrollContainer) scrollContainer = findScrollContainer();
  if (!scrollContainer) return;
  if (!isNearBottom()) return; // respect the user reading
  scrollContainer.scrollTop = scrollContainer.scrollHeight;
}

// A NEW message (user question or assistant turn) should ALWAYS bring the
// view to the bottom. nextTick ensures the new message is rendered into the
// DOM before we measure scrollHeight — without it, we'd scroll to the OLD
// bottom (before the new bubble grew the content), doing nothing.
function scrollToBottomForced() {
  nextTick(() => {
    if (!scrollContainer) scrollContainer = findScrollContainer();
    if (!scrollContainer) return;
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
  });
}

// New message added -> always follow it (after DOM update).
watch(() => props.messages.length, scrollToBottomForced);

// Streaming content of the last message — fires on every reveal-tick. Guard
// with isNearBottom so we don't yank the view while reading history.
watch(() => {
  if (props.messages.length === 0) return '';
  return props.messages[props.messages.length - 1].content;
}, () => {
  nextTick(() => scrollToBottom());
});

onMounted(() => {
  scrollContainer = findScrollContainer();
  scrollToBottomForced();
});
</script>

<template>
  <div class="message-list" ref="listRef">
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
/*
 * The empty-state welcome is now rendered by ChatArea's state-zero block.
 * Scroll is owned by .chat-scroll in ChatArea; this list just flows within it.
 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xl);
  padding: var(--spacing-sm);
}
</style>
