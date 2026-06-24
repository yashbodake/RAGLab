import { ref, computed } from 'vue';
import { useFeatures } from './useFeatures';
import { useMetrics } from './useMetrics';
import { useLogs } from './useLogs';
import { useChunks } from './useChunks';
import { useConversations } from './useConversations';

const isStreaming = ref(false);
const compareWithBaseline = ref(false);

export function useChat() {
  const { getFeaturePayload } = useFeatures();
  const { updateMetrics, updateBaseline, resetMetrics } = useMetrics();
  const { appendLogs, clearLogs } = useLogs();
  const { setChunks, clearChunks } = useChunks();
  const {
    conversations,
    activeConversation,
    activeId,
    ensureActive,
    addStreamingMessage,
    loadConversation,
    persist,
  } = useConversations();

  // messages is a computed view of the active conversation's messages, so the
  // chat view stays reactive when the user switches conversations in history.
  const messages = computed(() => activeConversation.value?.messages || []);

  function clearConversation() {
    isStreaming.value = false;
    clearLogs();
    clearChunks();
    resetMetrics();
  }

  async function sendQuery(queryText) {
    if (!queryText.trim() || isStreaming.value) return;

    // Reset metrics, logs, and chunks for the new query
    clearLogs();
    clearChunks();
    resetMetrics();

    // Ensure we have an active conversation to append to.
    const conv = ensureActive();

    // 1. Append User Message (persisted)
    const userMsg = {
      id: Date.now().toString() + '-user',
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString(),
      isStreaming: false,
    };
    conv.messages.push(userMsg);
    if (conv.title === 'New Conversation') {
      conv.title = queryText.slice(0, 40) + (queryText.length > 40 ? '…' : '');
    }

    // Build multi-turn history from prior turns (everything before this query).
    // Skip streaming/placeholder messages and cap to last 6 turns for token budget.
    const history = conv.messages
      .filter(m => m.id !== userMsg.id && m.content && !m.isStreaming)
      .slice(-6)
      .map(m => ({ role: m.role, content: m.content }));

    // 2. Append Placeholder Assistant Message (streaming)
    const assistantMsgId = Date.now().toString() + '-assistant';
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: null,
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    conv.messages.push(assistantMsg);
    persist();

    isStreaming.value = true;

    // Typewriter reveal queue — decouples token arrival speed from reveal
    // speed so the answer types out at a natural cadence (ChatGPT/Claude feel)
    // instead of dumping each SSE chunk instantly.
    let queuedChars = '';
    let revealDone = false;

    // Helper to find the live assistant message object in the active conv.
    const findAssistant = () => conv.messages.find(m => m.id === assistantMsgId);

    // Drain a few characters per tick at a steady cadence. Characters per tick
    // scales up slightly when the queue grows long, so a fast backend burst
    // doesn't make the reveal lag unreasonably behind.
    const REVEAL_INTERVAL_MS = 24;   // ~42fps — deliberate typing pace
    const BASE_CHARS_PER_TICK = 1;
    const revealTimer = setInterval(() => {
      const msg = findAssistant();
      if (!msg) return;
      if (queuedChars.length === 0) {
        // Queue empty — if the stream already finished, complete the reveal:
        // stop the timer and flip isStreaming off (cursor stops blinking).
        if (revealDone) {
          clearInterval(revealTimer);
          msg.isStreaming = false;
          isStreaming.value = false;
          persist();
        }
        return;
      }
      // Reveal more chars when falling behind so we never lag far behind the
      // backend while still looking like deliberate typing.
      const burst = queuedChars.length > 60 ? Math.ceil(queuedChars.length / 30) : BASE_CHARS_PER_TICK;
      const chunk = queuedChars.slice(0, burst);
      queuedChars = queuedChars.slice(burst);
      msg.content += chunk;
    }, REVEAL_INTERVAL_MS);

    try {
      const response = await fetch('/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          query: queryText,
          features: getFeaturePayload(),
          compare_with_baseline: compareWithBaseline.value,
          history,   // multi-turn context
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error ${response.status}` }));
        throw new Error(errorData.detail || 'Failed to submit query');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // Save the incomplete part to parse in the next iteration

        for (const part of parts) {
          if (!part.trim()) continue;

          let eventType = '';
          let dataStr = '';

          const lines = part.split('\n');
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.substring(5).trim();
            }
          }

          if (!eventType || !dataStr) continue;

          try {
            const data = JSON.parse(dataStr);

            if (eventType === 'classification') {
              // Store or log query classification metadata
            } else if (eventType === 'sources') {
              const msg = findAssistant();
              if (msg) msg.sources = data.chunks;
              setChunks(data.chunks, false);
            } else if (eventType === 'baseline_sources') {
              setChunks(data.chunks, true);
            } else if (eventType === 'token') {
              const msg = findAssistant();
              if (msg) {
                // Queue tokens for smooth typewriter reveal instead of dumping
                // each SSE chunk instantly (which reads as "appears all at once").
                queuedChars += data.text;
              }
            } else if (eventType === 'metrics') {
              updateMetrics(data);
            } else if (eventType === 'baseline_metrics') {
              updateBaseline(data);
            } else if (eventType === 'logs') {
              appendLogs(data.entries);
            } else if (eventType === 'error') {
              throw new Error(data.message || 'Stream processing error');
            } else if (eventType === 'done') {
              // Stream finished — let the reveal queue drain the rest, then
              // the finally block flips isStreaming off once revealed.
              revealDone = true;
            }
          } catch (e) {
            console.error('Error parsing SSE event payload:', e, dataStr);
          }
        }
      }
    } catch (err) {
      console.error('SSE Stream error:', err);
      clearInterval(revealTimer);
      const msg = findAssistant();
      if (msg) {
        // Flush whatever was queued so the error appears after typed text.
        msg.content += queuedChars + `\n\nSystem Error: ${err.message || 'Failed to complete RAG query pipeline.'}`;
        queuedChars = '';
        msg.isStreaming = false;
        isStreaming.value = false;
        persist();
      }
    } finally {
      // Mark the reveal eligible to complete. The revealTimer owns the final
      // isStreaming flip so the text types out fully before the cursor stops.
      // (Timer is cleared above on error.)
      revealDone = true;
    }
  }

  return {
    messages,
    isStreaming,
    compareWithBaseline,
    sendQuery,
    clearConversation
  };
}
