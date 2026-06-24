import { ref, computed } from 'vue';

const STORAGE_KEY = 'raglab.conversations.v1';

// Module-level singleton state — shared across all callers of useConversations.
const conversations = ref([]);
const activeId = ref(null);

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) conversations.value = JSON.parse(raw);
  } catch (e) {
    console.warn('Failed to load conversations from localStorage:', e);
    conversations.value = [];
  }
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.value));
  } catch (e) {
    console.warn('Failed to persist conversations:', e);
  }
}

// Load once on first use.
if (typeof window !== 'undefined' && conversations.value.length === 0) {
  load();
}

export function useConversations() {
  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) => b.updatedAt - a.updatedAt)
  );

  const activeConversation = computed(() =>
    conversations.value.find(c => c.id === activeId.value) || null
  );

  function createConversation() {
    const conv = {
      id: 'conv_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
      title: 'New Conversation',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    conversations.value.unshift(conv);
    activeId.value = conv.id;
    persist();
    return conv;
  }

  function ensureActive() {
    if (!activeConversation.value) {
      return createConversation();
    }
    return activeConversation.value;
  }

  function addMessage(role, content, sources = null) {
    const conv = ensureActive();
    const msg = {
      id: 'msg_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
      role,
      content,
      sources,
      isStreaming: false,
    };
    conv.messages.push(msg);
    // Auto-title from the first user message.
    if (conv.title === 'New Conversation' && role === 'user') {
      conv.title = content.slice(0, 40) + (content.length > 40 ? '…' : '');
    }
    conv.updatedAt = Date.now();
    persist();
    return msg;
  }

  // For streaming: we add a placeholder assistant message and return a handle
  // so useChat can mutate its content/isStreaming directly during streaming.
  function addStreamingMessage(role) {
    const conv = ensureActive();
    const msg = {
      id: 'msg_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
      role,
      content: '',
      sources: null,
      isStreaming: true,
    };
    conv.messages.push(msg);
    if (conv.title === 'New Conversation' && role === 'assistant') {
      // will be titled when user msg arrives
    }
    conv.updatedAt = Date.now();
    persist();
    return msg;
  }

  function loadConversation(id) {
    activeId.value = id;
  }

  function deleteConversation(id) {
    const idx = conversations.value.findIndex(c => c.id === id);
    if (idx !== -1) {
      conversations.value.splice(idx, 1);
      if (activeId.value === id) {
        activeId.value = conversations.value[0]?.id || null;
      }
      persist();
    }
  }

  function clearAll() {
    conversations.value = [];
    activeId.value = null;
    persist();
  }

  return {
    conversations: sortedConversations,
    activeId,
    activeConversation,
    createConversation,
    ensureActive,
    addMessage,
    addStreamingMessage,
    loadConversation,
    deleteConversation,
    clearAll,
  };
}
