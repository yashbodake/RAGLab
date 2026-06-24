import { ref } from 'vue';
import { useFeatures } from './useFeatures';
import { useMetrics } from './useMetrics';
import { useLogs } from './useLogs';
import { useChunks } from './useChunks';

const messages = ref([]);
const isStreaming = ref(false);
const compareWithBaseline = ref(false);

export function useChat() {
  const { getFeaturePayload } = useFeatures();
  const { updateMetrics, updateBaseline, resetMetrics } = useMetrics();
  const { appendLogs, clearLogs } = useLogs();
  const { setChunks, clearChunks } = useChunks();

  function clearConversation() {
    messages.value = [];
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

    // 1. Append User Message
    const userMsgId = Date.now().toString() + '-user';
    messages.value.push({
      id: userMsgId,
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString()
    });

    // 2. Append Placeholder Bot Message
    const assistantMsgId = Date.now().toString() + '-assistant';
    const assistantMsg = ref({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: null,
      timestamp: new Date().toISOString(),
      isStreaming: true
    });
    messages.value.push(assistantMsg.value);

    isStreaming.value = true;

    // Typewriter reveal queue — decouples token arrival speed from reveal
    // speed so the answer types out at a natural cadence (ChatGPT/Claude feel)
    // instead of dumping each SSE chunk instantly.
    let queuedChars = '';
    let revealDone = false;

    // Drain a few characters per tick at a steady cadence. Characters per tick
    // scales up slightly when the queue grows long, so a fast backend burst
    // doesn't make the reveal lag unreasonably behind.
    const REVEAL_INTERVAL_MS = 24;   // ~42fps — deliberate typing pace
    const BASE_CHARS_PER_TICK = 1;
    const revealTimer = setInterval(() => {
      const idx = messages.value.findIndex(m => m.id === assistantMsgId);
      if (idx === -1) return;
      if (queuedChars.length === 0) {
        // Queue empty — if the stream already finished, complete the reveal:
        // stop the timer and flip isStreaming off (cursor stops blinking).
        if (revealDone) {
          clearInterval(revealTimer);
          messages.value[idx].isStreaming = false;
          isStreaming.value = false;
        }
        return;
      }
      // Reveal more chars when falling behind so we never lag far behind the
      // backend while still looking like deliberate typing.
      const burst = queuedChars.length > 60 ? Math.ceil(queuedChars.length / 30) : BASE_CHARS_PER_TICK;
      const chunk = queuedChars.slice(0, burst);
      queuedChars = queuedChars.slice(burst);
      messages.value[idx].content += chunk;
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
          compare_with_baseline: compareWithBaseline.value
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
              // Find the assistant message in array and update it
              const idx = messages.value.findIndex(m => m.id === assistantMsgId);
              if (idx !== -1) {
                messages.value[idx].sources = data.chunks;
              }
              setChunks(data.chunks, false);
            } else if (eventType === 'baseline_sources') {
              setChunks(data.chunks, true);
            } else if (eventType === 'token') {
              const idx = messages.value.findIndex(m => m.id === assistantMsgId);
              if (idx !== -1) {
                // Queue tokens for smooth typewriter reveal instead of dumping
                // each SSE chunk instantly (which reads as "appears all at once").
                // The reveal loop below drains queuedChars at a natural cadence.
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
      const idx = messages.value.findIndex(m => m.id === assistantMsgId);
      if (idx !== -1) {
        // Flush whatever was queued so the error appears after typed text.
        messages.value[idx].content += queuedChars + `\n\nSystem Error: ${err.message || 'Failed to complete RAG query pipeline.'}`;
        queuedChars = '';
        messages.value[idx].isStreaming = false;
        isStreaming.value = false;
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
