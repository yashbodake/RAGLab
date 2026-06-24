<script setup>
import { useConversations } from '../composables/useConversations';
import { useChat } from '../composables/useChat';

const {
  conversations,
  activeId,
  loadConversation,
  deleteConversation,
  createConversation,
} = useConversations();
const { setActiveConversation, syncMessages } = useChat();

function fmtTime(ts) {
  const d = new Date(ts);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function selectConv(id) {
  // setActiveConversation loads it AND syncs the chat's messages ref.
  setActiveConversation(id);
}

function newChat() {
  createConversation();
  syncMessages();
}
</script>

<template>
  <div class="history-list">
    <button class="new-chat-btn" @click="newChat">
      <span class="material-symbols-outlined">add</span>
      <span>NEW CONVERSATION</span>
    </button>

    <div v-if="conversations.length === 0" class="empty">
      <span class="material-symbols-outlined">forum</span>
      <p>No saved conversations yet.<br/>Ask a question to start.</p>
    </div>

    <ul v-else class="conv-list">
      <li
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-item"
        :class="{ active: conv.id === activeId }"
        @click="selectConv(conv.id)"
      >
        <div class="conv-main">
          <span class="conv-title">{{ conv.title }}</span>
          <span class="conv-meta">
            <span class="conv-count">{{ conv.messages.filter(m => m.role === 'user').length }} msgs</span>
            <span class="conv-dot">·</span>
            <span class="conv-time">{{ fmtTime(conv.updatedAt) }}</span>
          </span>
        </div>
        <button
          class="conv-delete"
          aria-label="Delete conversation"
          @click.stop="deleteConversation(conv.id)"
        >
          <span class="material-symbols-outlined">delete</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  background: var(--accent-primary);
  color: var(--bg-primary);
  border: 1px solid var(--accent-primary);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.new-chat-btn:hover {
  background: var(--accent-secondary);
  border-color: var(--accent-secondary);
}
.new-chat-btn .material-symbols-outlined { font-size: 18px; }

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-2xl) var(--spacing-md);
  color: var(--text-dim);
  text-align: center;
}
.empty .material-symbols-outlined { font-size: 32px; opacity: 0.5; }
.empty p {
  font-family: var(--font-body);
  font-size: 0.82rem;
  line-height: 1.5;
}

.conv-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 60vh;
  overflow-y: auto;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.conv-item:hover {
  background: rgba(7, 54, 66, 0.04);
  border-color: rgba(7, 54, 66, 0.12);
}
.conv-item.active {
  background: rgba(203, 75, 22, 0.06);
  border-color: rgba(203, 75, 22, 0.3);
}

.conv-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.conv-title {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-meta {
  display: flex;
  gap: 4px;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-dim);
}
.conv-item.active .conv-title { color: var(--accent-secondary); }

.conv-delete {
  background: none;
  border: none;
  color: var(--text-dim);
  padding: 2px;
  cursor: pointer;
  display: flex;
  opacity: 0;
  transition: all var(--transition-fast);
}
.conv-item:hover .conv-delete { opacity: 1; }
.conv-delete:hover { color: var(--accent-error); }
.conv-delete .material-symbols-outlined { font-size: 16px; }
</style>
