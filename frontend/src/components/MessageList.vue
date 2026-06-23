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
  gap: var(--spacing-xl);
  padding: var(--spacing-sm);
}
</style>
