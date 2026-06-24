<script setup>
import { ref, watch, onMounted } from 'vue';
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
// view to the bottom — the user just acted, so they expect to see the result.
// This is intentionally separate from the guarded streaming scroll below.
function scrollToBottomForced() {
  if (!scrollContainer) scrollContainer = findScrollContainer();
  if (!scrollContainer) return;
  scrollContainer.scrollTop = scrollContainer.scrollHeight;
}

// New message added -> always follow it.
watch(() => props.messages.length, scrollToBottomForced);

// Watch the streaming content of the last message — this fires on every
// reveal-tick update. Here we DO respect the "near bottom" guard so we don't
// yank the view away while the user scrolls up to read earlier content.
watch(() => {
  if (props.messages.length === 0) return '';
  return props.messages[props.messages.length - 1].content;
}, scrollToBottom);

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
